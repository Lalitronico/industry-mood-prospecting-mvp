"""Tests for send_drafts CLI safety gates."""

import pytest

import send_drafts


def test_resend_mode_requires_explicit_confirmation(monkeypatch, capsys):
    called = False

    def fake_send_approved(*args, **kwargs):
        nonlocal called
        called = True
        return 0

    monkeypatch.setattr(send_drafts, "send_approved", fake_send_approved)

    with pytest.raises(SystemExit) as exc:
        send_drafts.main([
            "--mode", "resend",
            "--from-email", "Industry Mood <hola@industrymood.com>",
            "--limit", "1",
        ])

    assert exc.value.code == 2
    assert called is False
    assert "--confirm-send SEND" in capsys.readouterr().err


def test_resend_mode_requires_limit(monkeypatch, capsys):
    called = False

    def fake_send_approved(*args, **kwargs):
        nonlocal called
        called = True
        return 0

    monkeypatch.setenv("RESEND_API_KEY", "test_key")
    monkeypatch.setattr(send_drafts, "send_approved", fake_send_approved)

    with pytest.raises(SystemExit) as exc:
        send_drafts.main([
            "--mode", "resend",
            "--from-email", "Industry Mood <hola@industrymood.com>",
            "--confirm-send", "SEND",
        ])

    assert exc.value.code == 2
    assert called is False
    assert "--limit" in capsys.readouterr().err


def test_resend_mode_passes_limit_to_sender(monkeypatch):
    captured = {}

    class FakeResendBackend:
        def __init__(self, api_key=None, from_email=None, reply_to=None):
            captured["api_key"] = api_key
            captured["from_email"] = from_email
            captured["reply_to"] = reply_to

    def fake_send_approved(db_path, backend, limit=None):
        captured["db_path"] = db_path
        captured["backend"] = backend
        captured["limit"] = limit
        return 1

    monkeypatch.setenv("RESEND_API_KEY", "test_key")
    monkeypatch.setattr(send_drafts, "ResendBackend", FakeResendBackend)
    monkeypatch.setattr(send_drafts, "send_approved", fake_send_approved)

    send_drafts.main([
        "--db", "queue.db",
        "--mode", "resend",
        "--from-email", "Industry Mood <hola@industrymood.com>",
        "--reply-to", "lalo@industrymood.com",
        "--limit", "3",
        "--confirm-send", "SEND",
    ])

    assert captured["db_path"] == "queue.db"
    assert captured["from_email"] == "Industry Mood <hola@industrymood.com>"
    assert captured["reply_to"] == "lalo@industrymood.com"
    assert captured["limit"] == 3
