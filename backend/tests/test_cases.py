from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.activity_history import ActivityHistory
from app.models.case import Case, CategoryEnum, PriorityEnum, StatusEnum
from app.models.user import User
from tests.conftest import auth_headers, login


def create_case(client: TestClient, token: str) -> dict:
    response = client.post(
        "/cases",
        headers=auth_headers(token),
        json={
            "title": "Cannot access account",
            "description": "My password is not working and I cannot log in.",
            "category": "Account",
            "priority": "High",
            "due_date": None,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_valid_case_can_be_created(client: TestClient):
    requester_token = login(client, "requester@example.com", "Requester123!")
    case = create_case(client, requester_token)

    assert case["title"] == "Cannot access account"
    assert case["category"] == "Account"
    assert case["priority"] == "High"
    assert case["status"] == "Open"


def test_invalid_status_transition_is_rejected(client: TestClient):
    requester_token = login(client, "requester@example.com", "Requester123!")
    agent_token = login(client, "agent@example.com", "Agent123!")

    case = create_case(client, requester_token)
    case_id = case["id"]

    claim_response = client.post(
        f"/cases/{case_id}/claim",
        headers=auth_headers(agent_token),
    )
    assert claim_response.status_code == 200

    response = client.patch(
        f"/cases/{case_id}",
        headers=auth_headers(agent_token),
        json={"status": "Closed"},
    )
    assert response.status_code == 400


def test_resolution_summary_is_required(client: TestClient):
    requester_token = login(client, "requester@example.com", "Requester123!")
    agent_token = login(client, "agent@example.com", "Agent123!")

    case = create_case(client, requester_token)
    case_id = case["id"]

    client.post(
        f"/cases/{case_id}/claim",
        headers=auth_headers(agent_token),
    )

    response = client.patch(
        f"/cases/{case_id}",
        headers=auth_headers(agent_token),
        json={"status": "Resolved"},
    )
    assert response.status_code == 400


def test_due_date_earlier_than_creation_time_is_rejected(client: TestClient):
    requester_token = login(client, "requester@example.com", "Requester123!")

    response = client.post(
        "/cases",
        headers=auth_headers(requester_token),
        json={
            "title": "Invalid due date",
            "description": "Due date is in the past.",
            "category": "Other",
            "priority": "Low",
            "due_date": "2000-01-01T00:00:00Z",
        },
    )
    assert response.status_code == 400


def test_reopen_reason_is_required(client: TestClient):
    requester_token = login(client, "requester@example.com", "Requester123!")
    agent_token = login(client, "agent@example.com", "Agent123!")

    case = create_case(client, requester_token)
    case_id = case["id"]

    client.post(f"/cases/{case_id}/claim", headers=auth_headers(agent_token))
    client.patch(
        f"/cases/{case_id}",
        headers=auth_headers(agent_token),
        json={
            "status": "Resolved",
            "resolution_summary": "Issue fixed.",
        },
    )

    response = client.post(
        f"/cases/{case_id}/reopen",
        headers=auth_headers(requester_token),
        params={"reason": ""},
    )
    assert response.status_code == 400


def test_closed_case_cannot_be_reopened(client: TestClient, db: Session):
    requester = db.query(User).filter_by(email="requester@example.com").first()
    agent = db.query(User).filter_by(email="agent@example.com").first()

    case = Case(
        title="Closed reopen test",
        description="Testing closed state.",
        category=CategoryEnum.OTHER,
        priority=PriorityEnum.MEDIUM,
        status=StatusEnum.RESOLVED,
        requester_id=requester.id,
        agent_id=agent.id,
        resolved_at=datetime.now(timezone.utc).replace(tzinfo=None),
        resolution_summary="Fixed.",
    )
    db.add(case)
    db.commit()

    case.status = StatusEnum.CLOSED
    db.commit()

    requester_token = login(client, "requester@example.com", "Requester123!")

    response = client.post(
        f"/cases/{case.id}/reopen",
        headers=auth_headers(requester_token),
        params={"reason": "Need it again"},
    )
    assert response.status_code == 400


def test_requester_can_reopen_recently_resolved_case(client: TestClient):
    requester_token = login(client, "requester@example.com", "Requester123!")
    agent_token = login(client, "agent@example.com", "Agent123!")

    case = create_case(client, requester_token)
    case_id = case["id"]

    client.post(f"/cases/{case_id}/claim", headers=auth_headers(agent_token))
    client.patch(
        f"/cases/{case_id}",
        headers=auth_headers(agent_token),
        json={
            "status": "Resolved",
            "resolution_summary": "Issue fixed.",
        },
    )

    response = client.post(
        f"/cases/{case_id}/reopen",
        headers=auth_headers(requester_token),
        params={"reason": "Problem came back"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "Open"


def test_requester_cannot_reopen_after_seven_days(client: TestClient, db: Session):
    requester = db.query(User).filter_by(email="requester@example.com").first()
    agent = db.query(User).filter_by(email="agent@example.com").first()

    case = Case(
        title="Expired reopen test",
        description="Testing 7 day rule.",
        category=CategoryEnum.OTHER,
        priority=PriorityEnum.MEDIUM,
        status=StatusEnum.RESOLVED,
        requester_id=requester.id,
        agent_id=agent.id,
        resolved_at=(datetime.now(timezone.utc) - timedelta(days=8)).replace(tzinfo=None),
        resolution_summary="Fixed.",
    )
    db.add(case)
    db.commit()

    requester_token = login(client, "requester@example.com", "Requester123!")

    response = client.post(
        f"/cases/{case.id}/reopen",
        headers=auth_headers(requester_token),
        params={"reason": "Too late"},
    )
    assert response.status_code == 400