from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import RoleEnum, User

from tests.conftest import auth_headers, login


def test_invalid_password_returns_401(client: TestClient):
    response = client.post(
        "/auth/login",
        json={
            "username": "requester@example.com",
            "password": "WrongPassword123!",
        },
    )
    assert response.status_code == 401


def test_inactive_user_cannot_log_in(client: TestClient, db: Session):
    inactive_user = User(
        email="inactive@example.com",
        hashed_password=hash_password("Inactive123!"),
        role=RoleEnum.REQUESTER,
        is_active=False,
    )
    db.add(inactive_user)
    db.commit()

    response = client.post(
        "/auth/login",
        json={
            "username": "inactive@example.com",
            "password": "Inactive123!",
        },
    )
    assert response.status_code == 403