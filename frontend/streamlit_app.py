import os

import streamlit as st

from api_client.auth_api import get_current_user
from api_client.auth_api import login
from api_client.client import ApiClient


st.set_page_config(
    page_title="Support Case Management",
    layout="wide",
)


def initialize_session() -> None:
    defaults = {
        "token": None,
        "user": None,
        "api_base_url": os.getenv(
            "API_BASE_URL",
            "http://localhost:8000",
        ),
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def clear_session() -> None:
    st.session_state.token = None
    st.session_state.user = None


def get_api_client() -> ApiClient:
    return ApiClient(
        base_url=st.session_state.api_base_url,
        token=st.session_state.token,
    )


def show_login() -> None:
    st.title("Support Case Management")
    st.subheader("Sign in")

    with st.form("login_form"):
        username = st.text_input(
            "Email",
            placeholder="requester@example.com",
        )

        password = st.text_input(
            "Password",
            type="password",
        )

        submitted = st.form_submit_button(
            "Log in",
            use_container_width=True,
        )

    if submitted:
        if not username or not password:
            st.error(
                "Please enter both email and password.",
            )
            return

        try:
            temporary_api = ApiClient(
                base_url=st.session_state.api_base_url,
            )

            token_response = login(
                temporary_api,
                username,
                password,
            )

            token = token_response["access_token"]

            authenticated_api = ApiClient(
                base_url=st.session_state.api_base_url,
                token=token,
            )

            user = get_current_user(
                authenticated_api,
            )

            st.session_state.token = token
            st.session_state.user = user

            st.success("Login successful.")
            st.rerun()

        except ValueError as error:
            st.error(str(error))

        except Exception:
            st.error(
                "Could not connect to the API. "
                "Please check that FastAPI is running."
            )


def show_sidebar() -> None:
    user = st.session_state.user

    st.sidebar.success(
        f"Logged in as {user['email']}",
    )

    st.sidebar.write(
        f"Role: **{user['role']}**",
    )

    if st.sidebar.button(
        "Log out",
        use_container_width=True,
    ):
        clear_session()
        st.rerun()


initialize_session()

if st.session_state.user is None:
    show_login()
else:
    show_sidebar()

    st.title("Support Case Management")
    st.info(
        "Use the pages in the sidebar to manage cases."
    )