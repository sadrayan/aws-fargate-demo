from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_hello_returns_demo_payload() -> None:
    response = client.get("/hello")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert body.get("message") == "Hello from Fargate demo"


def test_burn_clamps_and_burns() -> None:
    response = client.get("/burn", params={"seconds": 0.01})
    assert response.status_code == 200
    assert response.json() == {"burned_seconds": 0.1}
