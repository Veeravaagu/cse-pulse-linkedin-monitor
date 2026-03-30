from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_ingest_mock() -> None:
    client = TestClient(app)
    response = client.post("/ingest/mock")
    assert response.status_code == 200
    payload = response.json()
    assert payload["ingested_count"] >= 1
