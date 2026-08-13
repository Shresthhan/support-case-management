from .client import ApiClient


def get_case_summary(
    api: ApiClient,
) -> dict:
    response = api.get(
        "/cases/admin/summary",
    )

    if response.status_code != 200:
        raise ValueError(
            api.error_message(response),
        )

    return response.json()