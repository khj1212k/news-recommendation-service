from fastapi.testclient import TestClient

from app.core.security import create_access_token, get_password_hash
from app.db.session import get_db
from app.main import app
from app.models.user import User


def test_event_logging(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    user = User(email="event@example.com", password_hash=get_password_hash("password123"))
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    token = create_access_token(str(user.id))

    client = TestClient(app)
    response = client.post(
        "/events",
        json={"event_type": "click", "context": {"page": "feed"}},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
