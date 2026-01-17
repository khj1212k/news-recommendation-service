from fastapi.testclient import TestClient

from app.db.session import get_db
from app.main import app


def test_signup_and_login(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.post("/auth/signup", json={"email": "user@example.com", "password": "strongpassword"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token

    response = client.post("/auth/login", json={"email": "user@example.com", "password": "strongpassword"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token
