"""Tests for safe sending guardrails."""

import os
import tempfile

import pytest

from queue_db import enqueue_draft, get_draft, init_queue, is_suppressed, update_status
from sender import DryRunBackend, send_approved


@pytest.fixture
def db_path():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def db(db_path):
    init_queue(db_path)
    return db_path


class CountingBackend:
    def __init__(self):
        self.sent = []

    def send(self, draft):
        self.sent.append(draft["email"])
        return True


def _draft(email):
    return {
        "subject": "Clima laboral",
        "body_text": "Mensaje aprobado",
        "template_key": "GM",
        "role_bucket": "GM",
        "company": "Aceros del Norte",
        "email": email,
        "contact_name": "Roberto Hernández",
    }


def test_send_approved_respects_limit(db):
    ids = []
    for email in ["a@empresa.mx", "b@empresa.mx", "c@empresa.mx"]:
        draft_id = enqueue_draft(db, _draft(email))
        update_status(db, draft_id, "approved")
        ids.append(draft_id)

    backend = CountingBackend()
    sent_count = send_approved(db, backend, limit=2)

    assert sent_count == 2
    assert backend.sent == ["a@empresa.mx", "b@empresa.mx"]
    assert get_draft(db, ids[0])["status"] == "sent"
    assert get_draft(db, ids[1])["status"] == "sent"
    assert get_draft(db, ids[2])["status"] == "approved"


def test_send_approved_suppresses_invalid_email_before_send(db):
    draft_id = enqueue_draft(db, _draft("persona@empresa"))
    update_status(db, draft_id, "approved")

    backend = CountingBackend()
    sent_count = send_approved(db, backend)

    assert sent_count == 0
    assert backend.sent == []
    assert get_draft(db, draft_id)["status"] == "suppressed"
    assert is_suppressed(db, "persona@empresa") is True


def test_send_approved_limit_counts_successful_sends_not_invalid_skips(db):
    bad_id = enqueue_draft(db, _draft("persona@empresa"))
    good_id = enqueue_draft(db, _draft("persona@empresa.com.mx"))
    update_status(db, bad_id, "approved")
    update_status(db, good_id, "approved")

    backend = CountingBackend()
    sent_count = send_approved(db, backend, limit=1)

    assert sent_count == 1
    assert backend.sent == ["persona@empresa.com.mx"]
    assert get_draft(db, bad_id)["status"] == "suppressed"
    assert get_draft(db, good_id)["status"] == "sent"
