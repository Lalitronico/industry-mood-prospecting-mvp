"""Tests for commercial viability features: opt-out, outcomes, reports, validation."""

import os
import tempfile

import pytest

from drafts import generate_draft
from queue_db import (
    enqueue_draft,
    get_draft,
    init_queue,
    mark_demo_booked,
    mark_not_interested,
    mark_positive_reply,
    update_status,
)
from reports import campaign_summary
from validators import has_valid_email_syntax


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


def _lead():
    return {
        "company": "Aceros del Norte",
        "contact_name": "Roberto Hernández",
        "role": "Director General",
        "email": "roberto@aceros.mx",
        "company_type": "Industria metalmecánica",
        "size": "AA",
        "city": "Chihuahua, Chih.",
    }


def _draft(email="roberto@aceros.mx", role_bucket="GM"):
    return {
        "subject": "Clima laboral",
        "body_text": "Mensaje aprobado",
        "template_key": role_bucket,
        "role_bucket": role_bucket,
        "company": "Aceros del Norte",
        "email": email,
        "contact_name": "Roberto Hernández",
    }


def test_generated_draft_contains_opt_out_and_sender_identity():
    draft = generate_draft(_lead())
    body = draft["body_text"].lower()
    assert "industry mood" in body
    assert "no desea recibir" in body or "dejar de recibir" in body
    assert "responda" in body and "remover" in body


def test_email_syntax_validator_accepts_normal_business_email():
    assert has_valid_email_syntax("persona@empresa.com.mx") is True


@pytest.mark.parametrize("email", ["", "persona", "persona@", "@empresa.com", "persona@empresa", "persona empresa@x.com"])
def test_email_syntax_validator_rejects_bad_addresses(email):
    assert has_valid_email_syntax(email) is False


def test_queue_schema_migrates_positive_reply_demo_and_not_interested(db):
    draft_id = enqueue_draft(db, _draft())
    mark_positive_reply(db, draft_id)
    draft = get_draft(db, draft_id)
    assert draft["status"] == "positive_reply"
    assert draft["positive_reply_at"] is not None

    mark_demo_booked(db, draft_id)
    draft = get_draft(db, draft_id)
    assert draft["status"] == "demo_booked"
    assert draft["demo_booked_at"] is not None

    second_id = enqueue_draft(db, _draft(email="otro@aceros.mx"))
    mark_not_interested(db, second_id)
    assert get_draft(db, second_id)["status"] == "not_interested"


def test_campaign_summary_counts_sent_replies_positive_and_demos(db):
    gm_id = enqueue_draft(db, _draft(role_bucket="GM"))
    hr_id = enqueue_draft(db, _draft(email="hr@empresa.mx", role_bucket="HR"))
    ops_id = enqueue_draft(db, _draft(email="ops@empresa.mx", role_bucket="OPS"))

    update_status(db, gm_id, "sent")
    update_status(db, hr_id, "replied")
    mark_positive_reply(db, ops_id)
    mark_demo_booked(db, ops_id)

    summary = campaign_summary(db)
    assert summary["total_drafts"] == 3
    assert summary["sent_or_later"] == 3
    assert summary["replied"] == 1
    assert summary["positive_reply"] == 0
    assert summary["demo_booked"] == 1
    assert summary["by_role"]["GM"]["sent_or_later"] == 1
    assert summary["by_role"]["HR"]["replied"] == 1
    assert summary["by_role"]["OPS"]["demo_booked"] == 1
