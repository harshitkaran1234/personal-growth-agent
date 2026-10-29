from fastapi.testclient import TestClient

from personal_growth_agent.main import app

client = TestClient(app)


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"success": True, "message": "healthy"}
