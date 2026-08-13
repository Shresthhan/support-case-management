import os

import requests


class ApiClient:
    def __init__(
        self,
        base_url: str | None = None,
        token: str | None = None,
    ):
        self.base_url = (
            base_url
            or os.getenv(
                "API_BASE_URL",
                "http://localhost:8000",
            )
        ).rstrip("/")

        self.token = token

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }

        if self.token:
            headers["Authorization"] = (
                f"Bearer {self.token}"
            )

        return headers

    def request(
        self,
        method: str,
        path: str,
        **kwargs,
    ) -> requests.Response:
        url = f"{self.base_url}{path}"

        headers = kwargs.pop(
            "headers",
            self._headers(),
        )

        return requests.request(
            method=method,
            url=url,
            headers=headers,
            timeout=15,
            **kwargs,
        )

    def get(self, path: str, **kwargs):
        return self.request(
            "GET",
            path,
            **kwargs,
        )

    def post(self, path: str, **kwargs):
        return self.request(
            "POST",
            path,
            **kwargs,
        )

    def patch(self, path: str, **kwargs):
        return self.request(
            "PATCH",
            path,
            **kwargs,
        )

    def delete(self, path: str, **kwargs):
        return self.request(
            "DELETE",
            path,
            **kwargs,
        )

    @staticmethod
    def error_message(response: requests.Response) -> str:
        try:
            data = response.json()
            detail = data.get(
                "detail",
                "An unexpected API error occurred.",
            )

            if isinstance(detail, list):
                return "; ".join(
                    str(error) for error in detail
                )

            return str(detail)

        except ValueError:
            return (
                "The API returned an unexpected response."
            )