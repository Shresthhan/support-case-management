from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.core.database import get_db
from app.core.security import hash_password
from app.main import app
from app.models.user import RoleEnum, User


TEST_DATABASE_URL = "sqlite://"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture()
def db() -> Generator[Session, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    session = TestingSessionLocal()

    requester = User(
        email="requester@example.com",
        hashed_password=hash_password("Requester123!"),
        role=RoleEnum.REQUESTER,
        is_active=True,
    )

    agent = User(
        email="agent@example.com",
        hashed_password=hash_password("Agent123!"),
        role=RoleEnum.AGENT,
        is_active=True,
    )

    admin = User(
        email="admin@example.com",
        hashed_password=hash_password("Admin123!"),
        role=RoleEnum.ADMIN,
        is_active=True,
    )

    session.add_all([requester, agent, admin])
    session.commit()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def client(db: Session) -> Generator[TestClient, None, None]:
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={
            "username": email,
            "password": password,
        },
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}