from .client import ApiClient


def login(
    api: ApiClient,
    username: str,
    password: str,
) -> dict:
    response = api.post(
        "/auth/login",
        json={
            "username": username,
            "password": password,
        },
    )

    if response.status_code != 200:
        raise ValueError(
            api.error_message(response),
        )

    return response.json()


def get_current_user(api: ApiClient) -> dict:
    response = api.get("/auth/me")

    if response.status_code != 200:
        raise ValueError(
            api.error_message(response),
        )

    return response.json()