from .client import ApiClient


def list_messages(
    api: ApiClient,
    case_id: int,
) -> list[dict]:
    response = api.get(
        f"/cases/{case_id}/messages",
    )

    if response.status_code != 200:
        raise ValueError(
            api.error_message(response),
        )

    data = response.json()

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        return data.get("items", [])

    return []


def add_public_reply(
    api: ApiClient,
    case_id: int,
    body: str,
) -> dict:
    response = api.post(
        f"/cases/{case_id}/messages/reply",
        json={
            "body": body,
        },
    )

    if response.status_code not in (200, 201):
        raise ValueError(
            api.error_message(response),
        )

    return response.json()


def add_internal_note(
    api: ApiClient,
    case_id: int,
    body: str,
) -> dict:
    response = api.post(
        f"/cases/{case_id}/messages/note",
        json={
            "body": body,
        },
    )

    if response.status_code not in (200, 201):
        raise ValueError(
            api.error_message(response),
        )

    return response.json()