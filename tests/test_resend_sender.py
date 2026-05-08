"""Tests for the Resend sender backend."""

import json

import pytest

from sender import ResendBackend


def _draft():
    return {
        "id": 7,
        "email": "rh@empresa.mx",
        "contact_name": "María RH",
        "subject": "Clima laboral",
        "body_text": "Mensaje aprobado",
    }


class _FakeResponse:
    def __init__(self, status=200, body=b'{"id":"email_123"}'):
        self.status = status
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_resend_backend_requires_api_key():
    with pytest.raises(ValueError):
        ResendBackend(api_key="")


def test_resend_backend_posts_expected_payload(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request, timeout))
        return _FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    backend = ResendBackend(api_key="test_key", from_email="Industry Mood <hola@industrymood.com>")

    assert backend.send(_draft()) is True
    request, timeout = calls[0]
    payload = json.loads(request.data.decode("utf-8"))
    assert request.full_url == "https://api.resend.com/emails"
    assert request.headers["Authorization"] == "Bearer test_key"
    assert payload["from"] == "Industry Mood <hola@industrymood.com>"
    assert payload["to"] == ["rh@empresa.mx"]
    assert payload["subject"] == "Clima laboral"
    assert payload["text"] == "Mensaje aprobado"
    assert timeout == 30


def test_resend_backend_returns_false_on_http_error(monkeypatch):
    def fake_urlopen(request, timeout):
        return _FakeResponse(status=429, body=b'{"message":"rate limited"}')

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    backend = ResendBackend(api_key="test_key", from_email="Industry Mood <hola@industrymood.com>")

    assert backend.send(_draft()) is False
