"""Tests for approval queue module — written before implementation (TDD)."""

import os
import sqlite3
import tempfile

import pytest

from queue_db import (
    init_queue, enqueue_draft, list_pending, update_status, get_draft,
    list_approved, mark_sent, find_existing_draft, enqueue_draft_once,
    has_terminal_status, is_suppressed, list_due_followup_sources,
    list_suppressions, mark_bounced, mark_replied, suppress_email,
)


# --- Fixtures ---

@pytest.fixture
def db_path():
    """Create a temp DB path, clean up after test."""
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)  # init_queue will create it
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def db(db_path):
    """Initialized queue DB path."""
    init_queue(db_path)
    return db_path


def _sample_draft():
    return {
        "subject": "Clima laboral en Aceros del Norte",
        "body_text": "Hola Roberto, le escribo porque...",
        "template_key": "GM",
        "role_bucket": "GM",
        "company": "Aceros del Norte, S.A. de C.V.",
        "email": "rhernandez@acerosnorte.com",
        "contact_name": "Lic. Roberto Hernández",
    }


# --- init_queue ---

class TestInitQueue:
    def test_creates_db_file(self, db_path):
        init_queue(db_path)
        assert os.path.exists(db_path)

    def test_creates_drafts_table(self, db_path):
        init_queue(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='drafts'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_creates_suppressions_table(self, db_path):
        init_queue(db_path)
        conn = sqlite3.connect(db_path)
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='suppressions'"
        )
        assert cursor.fetchone() is not None
        conn.close()

    def test_idempotent(self, db_path):
        """Calling init_queue twice should not raise."""
        init_queue(db_path)
        init_queue(db_path)

    def test_migrates_old_drafts_table(self, db_path):
        conn = sqlite3.connect(db_path)
        conn.executescript(
            """
            CREATE TABLE drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT NOT NULL,
                body_text TEXT NOT NULL,
                template_key TEXT NOT NULL,
                role_bucket TEXT NOT NULL,
                company TEXT NOT NULL,
                email TEXT NOT NULL,
                contact_name TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending_review',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                sent_at TEXT
            );
            """
        )
        conn.close()

        init_queue(db_path)

        conn = sqlite3.connect(db_path)
        columns = {row[1] for row in conn.execute("PRAGMA table_info(drafts)").fetchall()}
        conn.close()
        assert {"campaign_name", "step_number", "lead_key", "scheduled_at"}.issubset(columns)


# --- enqueue_draft ---

class TestEnqueueDraft:
    def test_returns_int_id(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        assert isinstance(draft_id, int)
        assert draft_id >= 1

    def test_sequential_ids(self, db):
        id1 = enqueue_draft(db, _sample_draft())
        id2 = enqueue_draft(db, _sample_draft())
        assert id2 == id1 + 1

    def test_default_status_is_pending(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        draft = get_draft(db, draft_id)
        assert draft["status"] == "pending_review"

    def test_stores_all_fields(self, db):
        sample = _sample_draft()
        draft_id = enqueue_draft(db, sample)
        draft = get_draft(db, draft_id)
        for key in ("subject", "body_text", "template_key", "role_bucket",
                     "company", "email", "contact_name"):
            assert draft[key] == sample[key], f"Mismatch on {key}"

    def test_stores_default_campaign_sequence_fields(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        draft = get_draft(db, draft_id)
        assert draft["campaign_name"] == "first_wave_local"
        assert draft["step_number"] == 1
        assert draft["lead_key"] == "rhernandez@acerosnorte.com"
        assert draft["scheduled_at"] is None


class TestIdempotentEnqueue:
    def test_find_existing_draft_returns_none_when_missing(self, db):
        assert find_existing_draft(db, _sample_draft()) is None

    def test_find_existing_draft_matches_email_case_insensitive(self, db):
        sample = _sample_draft()
        draft_id = enqueue_draft(db, sample)
        lookup = dict(sample)
        lookup["email"] = sample["email"].upper()
        existing = find_existing_draft(db, lookup)
        assert existing["id"] == draft_id

    def test_enqueue_draft_once_reuses_existing_id(self, db):
        sample = _sample_draft()
        first_id, first_created = enqueue_draft_once(db, sample)
        second_id, second_created = enqueue_draft_once(db, sample)
        assert first_created is True
        assert second_created is False
        assert second_id == first_id
        assert len(list_pending(db)) == 1

    def test_enqueue_draft_once_allows_different_sequence_step(self, db):
        sample = _sample_draft()
        follow_up = dict(sample)
        follow_up["step_number"] = 2
        first_id, first_created = enqueue_draft_once(db, sample)
        second_id, second_created = enqueue_draft_once(db, follow_up)
        assert first_created is True
        assert second_created is True
        assert second_id != first_id
        assert len(list_pending(db)) == 2


# --- list_pending ---

class TestListPending:
    def test_empty_queue(self, db):
        result = list_pending(db)
        assert result == []

    def test_returns_pending_only(self, db):
        id1 = enqueue_draft(db, _sample_draft())
        id2 = enqueue_draft(db, _sample_draft())
        update_status(db, id1, "approved")
        pending = list_pending(db)
        assert len(pending) == 1
        assert pending[0]["id"] == id2

    def test_pending_drafts_have_required_fields(self, db):
        enqueue_draft(db, _sample_draft())
        pending = list_pending(db)
        draft = pending[0]
        for key in ("id", "subject", "body_text", "company", "email",
                     "contact_name", "status", "template_key"):
            assert key in draft, f"Missing key: {key}"


# --- update_status ---

class TestUpdateStatus:
    def test_approve(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "approved")
        draft = get_draft(db, draft_id)
        assert draft["status"] == "approved"

    def test_reject(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "rejected")
        draft = get_draft(db, draft_id)
        assert draft["status"] == "rejected"

    def test_invalid_status_raises(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        with pytest.raises(ValueError):
            update_status(db, draft_id, "bogus_status")

    def test_suppress_status(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "suppressed")
        draft = get_draft(db, draft_id)
        assert draft["status"] == "suppressed"

    def test_replied_and_bounced_are_valid_terminal_statuses(self, db):
        id1 = enqueue_draft(db, _sample_draft())
        id2 = enqueue_draft(db, {**_sample_draft(), "email": "b@aceros.mx"})
        update_status(db, id1, "replied")
        update_status(db, id2, "bounced")
        assert get_draft(db, id1)["status"] == "replied"
        assert get_draft(db, id2)["status"] == "bounced"

    def test_nonexistent_id_raises(self, db):
        with pytest.raises(ValueError):
            update_status(db, 9999, "approved")


# --- get_draft ---

class TestGetDraft:
    def test_returns_dict(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        draft = get_draft(db, draft_id)
        assert isinstance(draft, dict)

    def test_nonexistent_returns_none(self, db):
        result = get_draft(db, 9999)
        assert result is None

    def test_has_created_at(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        draft = get_draft(db, draft_id)
        assert "created_at" in draft
        assert draft["created_at"] is not None


# --- sent status ---

class TestSentStatus:
    def test_update_to_sent(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "approved")
        update_status(db, draft_id, "sent")
        draft = get_draft(db, draft_id)
        assert draft["status"] == "sent"

    def test_sent_at_initially_none(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        draft = get_draft(db, draft_id)
        assert draft["sent_at"] is None


# --- list_approved ---

class TestListApproved:
    def test_returns_only_approved(self, db):
        id1 = enqueue_draft(db, _sample_draft())
        id2 = enqueue_draft(db, _sample_draft())
        id3 = enqueue_draft(db, _sample_draft())
        update_status(db, id1, "approved")
        update_status(db, id3, "rejected")
        # id2 stays pending
        approved = list_approved(db)
        assert len(approved) == 1
        assert approved[0]["id"] == id1

    def test_empty_when_none_approved(self, db):
        enqueue_draft(db, _sample_draft())
        assert list_approved(db) == []


# --- mark_sent ---

class TestMarkSent:
    def test_sets_status_and_timestamp(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "approved")
        mark_sent(db, draft_id)
        draft = get_draft(db, draft_id)
        assert draft["status"] == "sent"
        assert draft["sent_at"] is not None

    def test_accepts_explicit_sent_at(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "approved")
        mark_sent(db, draft_id, sent_at="2026-01-01T00:00:00+00:00")
        draft = get_draft(db, draft_id)
        assert draft["sent_at"] == "2026-01-01T00:00:00+00:00"

    def test_nonexistent_raises(self, db):
        with pytest.raises(ValueError):
            mark_sent(db, 9999)


# --- suppressions ---

class TestSuppressions:
    def test_suppress_email_adds_to_list(self, db):
        suppress_email(db, "Person@Example.com", reason="unsubscribed", source="manual")
        assert is_suppressed(db, "person@example.com") is True
        rows = list_suppressions(db)
        assert rows[0]["email"] == "person@example.com"
        assert rows[0]["reason"] == "unsubscribed"

    def test_suppress_email_updates_unsent_drafts(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "approved")
        affected = suppress_email(db, "RHERNANDEZ@ACEROSNORTE.COM", reason="unsubscribed")
        draft = get_draft(db, draft_id)
        assert affected == 1
        assert draft["status"] == "suppressed"
        assert list_approved(db) == []

    def test_suppress_email_does_not_change_sent_drafts(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "approved")
        mark_sent(db, draft_id)
        affected = suppress_email(db, "rhernandez@acerosnorte.com", reason="unsubscribed")
        draft = get_draft(db, draft_id)
        assert affected == 0
        assert draft["status"] == "sent"


# --- follow-up sequencing ---

class TestFollowUpSequencing:
    def test_step_two_due_after_four_days(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "approved")
        mark_sent(db, draft_id, sent_at="2026-01-01T00:00:00+00:00")
        due = list_due_followup_sources(db, 2, as_of="2026-01-05T00:00:00+00:00")
        assert len(due) == 1
        assert due[0]["id"] == draft_id

    def test_step_two_not_due_before_four_days(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "approved")
        mark_sent(db, draft_id, sent_at="2026-01-01T00:00:00+00:00")
        due = list_due_followup_sources(db, 2, as_of="2026-01-04T23:59:59+00:00")
        assert due == []

    def test_step_three_due_after_step_two_sent_for_seven_days(self, db):
        step_two = {**_sample_draft(), "step_number": 2}
        draft_id = enqueue_draft(db, step_two)
        update_status(db, draft_id, "approved")
        mark_sent(db, draft_id, sent_at="2026-01-01T00:00:00+00:00")
        due = list_due_followup_sources(db, 3, as_of="2026-01-08T00:00:00+00:00")
        assert len(due) == 1
        assert due[0]["id"] == draft_id

    def test_existing_later_step_blocks_duplicate_followup(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "approved")
        mark_sent(db, draft_id, sent_at="2026-01-01T00:00:00+00:00")
        enqueue_draft(db, {**_sample_draft(), "step_number": 2})
        due = list_due_followup_sources(db, 2, as_of="2026-01-05T00:00:00+00:00")
        assert due == []

    def test_replied_contact_blocks_followup_and_suppresses_unsent(self, db):
        step_one_id = enqueue_draft(db, _sample_draft())
        step_two_id = enqueue_draft(db, {**_sample_draft(), "step_number": 2})
        update_status(db, step_one_id, "approved")
        update_status(db, step_two_id, "approved")
        mark_sent(db, step_one_id, sent_at="2026-01-01T00:00:00+00:00")
        mark_replied(db, step_one_id)
        due = list_due_followup_sources(db, 2, as_of="2026-01-05T00:00:00+00:00")
        assert due == []
        assert has_terminal_status(db, "rhernandez@acerosnorte.com") is True
        assert get_draft(db, step_two_id)["status"] == "suppressed"

    def test_bounced_contact_blocks_followup_and_suppresses_email(self, db):
        draft_id = enqueue_draft(db, _sample_draft())
        update_status(db, draft_id, "approved")
        mark_sent(db, draft_id, sent_at="2026-01-01T00:00:00+00:00")
        mark_bounced(db, draft_id)
        due = list_due_followup_sources(db, 2, as_of="2026-01-05T00:00:00+00:00")
        assert due == []
        assert is_suppressed(db, "rhernandez@acerosnorte.com") is True
