"""Tests for approval queue module — written before implementation (TDD)."""

import os
import sqlite3
import tempfile

import pytest

from queue_db import (
    init_queue, enqueue_draft, list_pending, update_status, get_draft,
    list_approved, mark_sent,
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

    def test_idempotent(self, db_path):
        """Calling init_queue twice should not raise."""
        init_queue(db_path)
        init_queue(db_path)


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

    def test_nonexistent_raises(self, db):
        with pytest.raises(ValueError):
            mark_sent(db, 9999)
