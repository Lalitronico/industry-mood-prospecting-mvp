"""Tests for approved-draft CSV export — written before implementation (TDD)."""

import csv
import os
import tempfile

import pytest

from queue_db import init_queue, enqueue_draft, update_status
from export_approved import export_approved_csv


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


# --- export_approved_csv ---

class TestExportApprovedCsv:
    def test_returns_list_of_dicts(self, db):
        id1 = enqueue_draft(db, _sample())
        update_status(db, id1, "approved")
        rows = export_approved_csv(db)
        assert isinstance(rows, list)
        assert len(rows) == 1
        assert isinstance(rows[0], dict)

    def test_only_approved_drafts(self, db):
        id1 = enqueue_draft(db, _sample("A", "a@a.mx"))
        id2 = enqueue_draft(db, _sample("B", "b@b.mx"))
        id3 = enqueue_draft(db, _sample("C", "c@c.mx"))
        update_status(db, id1, "approved")
        # id2 stays pending
        update_status(db, id3, "rejected")
        rows = export_approved_csv(db)
        assert len(rows) == 1
        assert rows[0]["company"] == "A"

    def test_required_columns(self, db):
        id1 = enqueue_draft(db, _sample())
        update_status(db, id1, "approved")
        rows = export_approved_csv(db)
        expected_keys = {"id", "email", "contact_name", "company", "subject", "body_text", "status"}
        assert expected_keys.issubset(rows[0].keys())

    def test_empty_when_no_approved(self, db):
        enqueue_draft(db, _sample())
        rows = export_approved_csv(db)
        assert rows == []

    def test_write_csv_file(self, db, tmp_path):
        id1 = enqueue_draft(db, _sample())
        update_status(db, id1, "approved")
        csv_path = str(tmp_path / "approved.csv")
        export_approved_csv(db, output_path=csv_path)
        assert os.path.exists(csv_path)
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 1
        assert rows[0]["email"] == "a@aceros.mx"

    def test_csv_has_header(self, db, tmp_path):
        id1 = enqueue_draft(db, _sample())
        update_status(db, id1, "approved")
        csv_path = str(tmp_path / "approved.csv")
        export_approved_csv(db, output_path=csv_path)
        with open(csv_path, encoding="utf-8") as f:
            header = f.readline().strip()
        assert "id" in header
        assert "email" in header
