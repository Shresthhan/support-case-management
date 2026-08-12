from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.activity_history import ActivityHistory
from app.models.case import Case, CategoryEnum, PriorityEnum
from tests.conftest import auth_headers, login


def create_account_case(client: TestClient) -> int:
    requester_token = login(client, "requester@example.com", "Requester123!")

    response = client.post(
        "/cases",
        headers=auth_headers(requester_token),
        json={
            "title": "Cannot login to account",
            "description": "My password is not working and I cannot access the portal.",
            "category": "Other",
            "priority": "Low",
            "due_date": None,
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_ai_suggestion_does_not_auto_change_case(client: TestClient, db: Session):
    case_id = create_account_case(client)
    agent_token = login(client, "agent@example.com", "Agent123!")

    response = client.post(
        f"/cases/{case_id}/triage/suggest",
        headers=auth_headers(agent_token),
    )
    assert response.status_code == 200

    case = db.query(Case).filter(Case.id == case_id).first()
    assert case.category == CategoryEnum.OTHER
    assert case.priority == PriorityEnum.LOW


def test_ai_suggestion_is_applied_only_after_confirmation(client: TestClient, db: Session):
    case_id = create_account_case(client)
    agent_token = login(client, "agent@example.com", "Agent123!")

    suggestion_response = client.post(
        f"/cases/{case_id}/triage/suggest",
        headers=auth_headers(agent_token),
    )
    assert suggestion_response.status_code == 200

    suggestion = suggestion_response.json()

    apply_response = client.post(
        f"/cases/{case_id}/triage/apply",
        headers=auth_headers(agent_token),
        json={
            "suggestion": suggestion,
            "apply_request": {
                "apply_category": True,
                "apply_priority": True,
                "apply_summary": False,
            },
        },
    )
    assert apply_response.status_code == 200

    history = db.query(ActivityHistory).filter(
        ActivityHistory.case_id == case_id,
        ActivityHistory.event_type == "triage_suggestion_applied",
    ).first()

    assert history is not None

def test_ai_timeout_does_not_break_normal_case_workflow(
    client: TestClient,
    monkeypatch,
):
    case_id = create_account_case(client)

    agent_token = login(
        client,
        "agent@example.com",
        "Agent123!",
    )

    def fake_timeout(*args, **kwargs):
        raise TimeoutError("Mock AI timeout")

    monkeypatch.setattr(
        "app.ai.triage_service.generate_mock_suggestion",
        fake_timeout,
    )

    triage_response = client.post(
        f"/cases/{case_id}/triage/suggest",
        headers=auth_headers(agent_token),
    )

    assert triage_response.status_code == 503

    requester_token = login(
        client,
        "requester@example.com",
        "Requester123!",
    )

    normal_case_response = client.get(
        f"/cases/{case_id}",
        headers=auth_headers(requester_token),
    )

    assert normal_case_response.status_code == 200

def test_invalid_ai_response_is_handled_safely(
    client: TestClient,
    monkeypatch,
):
    case_id = create_account_case(client)

    agent_token = login(
        client,
        "agent@example.com",
        "Agent123!",
    )

    def fake_invalid_response(*args, **kwargs):
        return {
            "category": "InvalidCategory",
            "priority": "InvalidPriority",
        }

    monkeypatch.setattr(
        "app.ai.triage_service.generate_mock_suggestion",
        fake_invalid_response,
    )

    triage_response = client.post(
        f"/cases/{case_id}/triage/suggest",
        headers=auth_headers(agent_token),
    )

    assert triage_response.status_code == 503

    requester_token = login(
        client,
        "requester@example.com",
        "Requester123!",
    )

    normal_case_response = client.get(
        f"/cases/{case_id}",
        headers=auth_headers(requester_token),
    )

    assert normal_case_response.status_code == 200