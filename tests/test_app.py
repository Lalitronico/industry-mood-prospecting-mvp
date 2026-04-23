"""Smoke tests for the FastAPI app."""

from fastapi.testclient import TestClient


def test_health_check_starts_app(tmp_path, monkeypatch):
    db_path = tmp_path / "industry_mood_test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    from app.main import app

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
