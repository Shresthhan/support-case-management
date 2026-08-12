from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.activity_history import ActivityHistory
from tests.conftest import auth_headers, login


def test_case_creation_creates_activity_history(client: TestClient, db: Session):
    requester_token = login(client, "requester@example.com", "Requester123!")

    response = client.post(
        "/cases",
        headers=auth_headers(requester_token),
        json={
            "title": "History test case",
            "description": "Testing activity history.",
            "category": "Technical",
            "priority": "Medium",
            "due_date": None,
        },
    )
    assert response.status_code == 201
    case_id = response.json()["id"]

    history = db.query(ActivityHistory).filter(
        ActivityHistory.case_id == case_id
    ).all()

    assert len(history) >= 1
    assert history[0].event_type == "case_created"


def test_public_reply_creates_activity_history(client: TestClient, db: Session):
    requester_token = login(client, "requester@example.com", "Requester123!")

    create_response = client.post(
        "/cases",
        headers=auth_headers(requester_token),
        json={
            "title": "Reply history case",
            "description": "Testing reply history.",
            "category": "Other",
            "priority": "Low",
            "due_date": None,
        },
    )
    case_id = create_response.json()["id"]

    reply_response = client.post(
        f"/cases/{case_id}/messages/reply",
        headers=auth_headers(requester_token),
        json={"body": "This is a public follow-up."},
    )
    assert reply_response.status_code == 201

    history = db.query(ActivityHistory).filter(
        ActivityHistory.case_id == case_id,
        ActivityHistory.event_type == "public_reply_added",
    ).first()

    assert history is not None