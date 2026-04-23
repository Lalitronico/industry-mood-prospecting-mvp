"""Tests for sender abstraction — written before implementation (TDD)."""

import os
import tempfile

import pytest

from queue_db import init_queue, enqueue_draft, update_status, get_draft, suppress_email
from sender import send_approved, DryRunBackend, FileOutboxBackend


# --- Fixtures ---

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


def _sample(company="Aceros Norte", email="a@aceros.mx"):
    return {
        "subject": "Clima laboral en " + company,
        "body_text": "Estimado/a contacto...",
        "template_key": "GM",
        "role_bucket": "GM",
        "company": company,
        "email": email,
        "contact_name": "Roberto Hernández",
    }


def _approve(db, draft_id):
    update_status(db, draft_id, "approved")


# --- DryRunBackend ---

class TestDryRunBackend:
    def test_send_returns_true(self):
        backend = DryRunBackend()
        result = backend.send({"email": "x@y.com", "subject": "Hi", "body_text": "..."})
        assert result is True

    def test_logs_output(self, capsys):
        backend = DryRunBackend()
        backend.send({"email": "x@y.com", "subject": "Hola", "body_text": "cuerpo"})
        captured = capsys.readouterr()
        assert "x@y.com" in captured.out
        assert "Hola" in captured.out


# --- FileOutboxBackend ---

class TestFileOutboxBackend:
    def test_creates_outbox_dir(self, tmp_path):
        outbox = str(tmp_path / "outbox")
        backend = FileOutboxBackend(outbox)
        backend.send({"id": 1, "email": "a@b.mx", "subject": "S", "body_text": "B", "contact_name": "N"})
        assert os.path.isdir(outbox)

    def test_writes_eml_file(self, tmp_path):
        outbox = str(tmp_path / "outbox")
        backend = FileOutboxBackend(outbox)
        backend.send({"id": 7, "email": "a@b.mx", "subject": "S", "body_text": "B", "contact_name": "N"})
        files = os.listdir(outbox)
        assert len(files) == 1
        assert files[0].endswith(".txt")

    def test_eml_contains_fields(self, tmp_path):
        outbox = str(tmp_path / "outbox")
        backend = FileOutboxBackend(outbox)
        backend.send({
            "id": 3,
            "email": "cto@factory.mx",
            "subject": "Clima laboral",
            "body_text": "Estimado contacto...",
            "contact_name": "Luis",
        })
        files = os.listdir(outbox)
        content = open(os.path.join(outbox, files[0]), encoding="utf-8").read()
        assert "cto@factory.mx" in content
        assert "Clima laboral" in content
        assert "Estimado contacto..." in content

    def test_send_returns_true(self, tmp_path):
        outbox = str(tmp_path / "outbox")
        backend = FileOutboxBackend(outbox)
        result = backend.send({"id": 1, "email": "a@b.mx", "subject": "S", "body_text": "B", "contact_name": "N"})
        assert result is True


# --- send_approved integration ---

class TestSendApproved:
    def test_sends_only_approved(self, db):
        id1 = enqueue_draft(db, _sample("A", "a@a.mx"))
        id2 = enqueue_draft(db, _sample("B", "b@b.mx"))
        _approve(db, id1)
        # id2 stays pending
        backend = DryRunBackend()
        sent_count = send_approved(db, backend)
        assert sent_count == 1

    def test_marks_sent_after_processing(self, db):
        id1 = enqueue_draft(db, _sample())
        _approve(db, id1)
        backend = DryRunBackend()
        send_approved(db, backend)
        draft = get_draft(db, id1)
        assert draft["status"] == "sent"

    def test_sent_at_is_set(self, db):
        id1 = enqueue_draft(db, _sample())
        _approve(db, id1)
        backend = DryRunBackend()
        send_approved(db, backend)
        draft = get_draft(db, id1)
        assert draft["sent_at"] is not None

    def test_zero_when_nothing_approved(self, db):
        enqueue_draft(db, _sample())
        backend = DryRunBackend()
        sent_count = send_approved(db, backend)
        assert sent_count == 0

    def test_does_not_resend_already_sent(self, db):
        id1 = enqueue_draft(db, _sample())
        _approve(db, id1)
        backend = DryRunBackend()
        send_approved(db, backend)
        sent_count = send_approved(db, backend)
        assert sent_count == 0

    def test_file_outbox_integration(self, db, tmp_path):
        id1 = enqueue_draft(db, _sample())
        _approve(db, id1)
        outbox = str(tmp_path / "outbox")
        backend = FileOutboxBackend(outbox)
        sent_count = send_approved(db, backend)
        assert sent_count == 1
        assert len(os.listdir(outbox)) == 1
        draft = get_draft(db, id1)
        assert draft["status"] == "sent"

    def test_suppressed_approved_draft_is_not_sent(self, db):
        id1 = enqueue_draft(db, _sample())
        _approve(db, id1)
        suppress_email(db, "a@aceros.mx", reason="unsubscribed")
        backend = DryRunBackend()
        sent_count = send_approved(db, backend)
        draft = get_draft(db, id1)
        assert sent_count == 0
        assert draft["status"] == "suppressed"

    def test_replied_contact_blocks_approved_followup_send(self, db):
        id1 = enqueue_draft(db, _sample())
        id2 = enqueue_draft(db, {**_sample(), "step_number": 2})
        update_status(db, id1, "replied")
        _approve(db, id2)
        backend = DryRunBackend()
        sent_count = send_approved(db, backend)
        assert sent_count == 0
        assert get_draft(db, id2)["status"] == "suppressed"
