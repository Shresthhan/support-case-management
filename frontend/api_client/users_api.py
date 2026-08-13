from .client import ApiClient


def list_users(api: ApiClient) -> list[dict]:
    response = api.get("/users")

    if response.status_code != 200:
        raise ValueError(
            api.error_message(response),
        )

    data = response.json()

    if isinstance(data, list):
        return data

    return []


def list_active_agents(api: ApiClient) -> list[dict]:
    users = list_users(api)

    return [
        user
        for user in users
        if str(user.get("role", "")).lower()
        == "agent"
        and user.get("is_active", False)
    ]


def create_user(
    api: ApiClient,
    email: str,
    password: str,
    role: str,
) -> dict:
    response = api.post(
        "/users",
        json={
            "email": email,
            "password": password,
            "role": role,
        },
    )

    if response.status_code not in (200, 201):
        raise ValueError(
            api.error_message(response),
        )

    return response.json()


def update_user(
    api: ApiClient,
    user_id: int,
    payload: dict,
) -> dict:
    response = api.patch(
        f"/users/{user_id}",
        json=payload,
    )

    if response.status_code not in (200, 201):
        raise ValueError(
            api.error_message(response),
        )

    return response.json()


def deactivate_user(
    api: ApiClient,
    user_id: int,
) -> dict:
    response = api.post(
        f"/users/{user_id}/deactivate",
    )

    if response.status_code not in (200, 201):
        raise ValueError(
            api.error_message(response),
        )

    return response.json()