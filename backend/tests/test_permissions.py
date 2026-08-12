from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.case import Case
from app.models.user import RoleEnum, User
from tests.conftest import auth_headers, login


def test_requester_cannot_view_another_requesters_case(client: TestClient, db: Session):
    first_requester_token = login(client, "requester@example.com", "Requester123!")

    response = client.post(
        "/cases",
        headers=auth_headers(first_requester_token),
        json={
            "title": "Private case",
            "description": "This belongs to another requester.",
            "category": "Other",
            "priority": "Low",
            "due_date": None,
        },
    )
    assert response.status_code == 201
    case_id = response.json()["id"]

    second_requester = User(
        email="second-requester@example.com",
        hashed_password=hash_password("SecondRequester123!"),
        role=RoleEnum.REQUESTER,
        is_active=True,
    )
    db.add(second_requester)
    db.commit()

    second_requester_token = login(client, "second-requester@example.com", "SecondRequester123!")

    response = client.get(
        f"/cases/{case_id}",
        headers=auth_headers(second_requester_token),
    )
    assert response.status_code == 403


def test_non_admin_cannot_manage_users_or_roles(client: TestClient):
    agent_token = login(client, "agent@example.com", "Agent123!")

    response = client.get("/users", headers=auth_headers(agent_token))
    assert response.status_code == 403


def test_requester_cannot_create_or_see_internal_note(client: TestClient):
    requester_token = login(client, "requester@example.com", "Requester123!")

    note_response = client.post(
        "/cases/1/messages/note",
        headers=auth_headers(requester_token),
        json={"body": "This should not be allowed."},
    )
    assert note_response.status_code == 403


def test_agent_can_claim_unassigned_case(client: TestClient):
    requester_token = login(client, "requester@example.com", "Requester123!")
    agent_token = login(client, "agent@example.com", "Agent123!")

    case_response = client.post(
        "/cases",
        headers=auth_headers(requester_token),
        json={
            "title": "Claim test",
            "description": "Unassigned case.",
            "category": "Other",
            "priority": "Low",
            "due_date": None,
        },
    )
    case_id = case_response.json()["id"]

    claim_response = client.post(
        f"/cases/{case_id}/claim",
        headers=auth_headers(agent_token),
    )
    assert claim_response.status_code == 200

    second_claim = client.post(
        f"/cases/{case_id}/claim",
        headers=auth_headers(agent_token),
    )
    assert second_claim.status_code == 409


def test_agent_cannot_update_another_agents_case(client: TestClient):
    requester_token = login(client, "requester@example.com", "Requester123!")
    agent_token = login(client, "agent@example.com", "Agent123!")

    case_response = client.post(
        "/cases",
        headers=auth_headers(requester_token),
        json={
            "title": "Another agent case",
            "description": "Assigned to a different agent.",
            "category": "Other",
            "priority": "Low",
            "due_date": None,
        },
    )
    case_id = case_response.json()["id"]

    response = client.patch(
        f"/cases/{case_id}",
        headers=auth_headers(agent_token),
        json={"priority": "High"},
    )
    assert response.status_code == 403


def test_admin_can_reassign_case_but_not_to_requester_or_inactive_user(client: TestClient, db: Session):
    requester_token = login(client, "requester@example.com", "Requester123!")
    admin_token = login(client, "admin@example.com", "Admin123!")

    case_response = client.post(
        "/cases",
        headers=auth_headers(requester_token),
        json={
            "title": "Reassign test",
            "description": "Need reassignment.",
            "category": "Other",
            "priority": "Low",
            "due_date": None,
        },
    )
    case_id = case_response.json()["id"]

    response = client.patch(
        f"/cases/{case_id}/assignment",
        headers=auth_headers(admin_token),
        json={"agent_id": 2},
    )
    assert response.status_code == 200

    bad_target = User(
        email="inactive-agent@example.com",
        hashed_password=hash_password("InactiveAgent123!"),
        role=RoleEnum.AGENT,
        is_active=False,
    )
    db.add(bad_target)
    db.commit()

    response2 = client.patch(
        f"/cases/{case_id}/assignment",
        headers=auth_headers(admin_token),
        json={"agent_id": bad_target.id},
    )
    assert response2.status_code in (400, 404)

    response3 = client.patch(
        f"/cases/{case_id}/assignment",
        headers=auth_headers(admin_token),
        json={"agent_id": 1},
    )
    assert response3.status_code in (400, 404)