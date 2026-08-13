from .client import ApiClient


def list_agent_queue(
    api: ApiClient,
    status: str | None = None,
) -> list[dict]:
    params = {}

    if status:
        params["status"] = status

    response = api.get(
        "/cases/agent-queue",
        params=params,
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


def claim_case(
    api: ApiClient,
    case_id: int,
) -> dict:
    response = api.post(
        f"/cases/{case_id}/claim",
    )

    if response.status_code not in (200, 201):
        raise ValueError(
            api.error_message(response),
        )

    return response.json()


def update_case(
    api: ApiClient,
    case_id: int,
    payload: dict,
) -> dict:
    response = api.patch(
        f"/cases/{case_id}",
        json=payload,
    )

    if response.status_code not in (200, 201):
        raise ValueError(
            api.error_message(response),
        )

    return response.json()