import streamlit as st

from api_client.agent_api import claim_case
from api_client.agent_api import list_agent_queue
from api_client.client import ApiClient


st.set_page_config(
    page_title="Agent Queue",
    page_icon="🧑‍💻",
    layout="wide",
)


def require_login() -> None:
    if st.session_state.get("user") is None:
        st.warning("Please log in first.")
        st.stop()


def create_api_client() -> ApiClient:
    return ApiClient(
        base_url=st.session_state.api_base_url,
        token=st.session_state.token,
    )


def show_case_row(api: ApiClient, case: dict) -> None:
    col1, col2, col3, col4 = st.columns([3, 2, 2, 2])

    with col1:
        st.write(
            f"**{case.get('case_number', 'Case')}**"
        )
        st.write(case.get("title", ""))

    with col2:
        st.write(
            f"Status: {case.get('status', '—')}"
        )

    with col3:
        st.write(
            f"Priority: {case.get('priority', '—')}"
        )

    with col4:
        if st.button(
            "Claim",
            key=f"claim_{case['id']}",
            use_container_width=True,
        ):
            try:
                claim_case(api, case["id"])
                st.success("Case claimed.")
                st.rerun()
            except ValueError as error:
                st.error(str(error))
            except Exception:
                st.error("Could not claim the case.")


require_login()

user = st.session_state.user
role = str(user.get("role", "")).lower()

if role not in {"agent", "admin"}:
    st.error("This page is for agents only.")
    st.stop()

st.title("Agent Queue")

api = create_api_client()

status_options = [
    "Open",
    "In Progress",
    "Waiting for Requester",
    "Resolved",
    "Closed",
]

selected_status = st.selectbox(
    "Filter by status",
    options=["All"] + status_options,
)

status_filter = None
if selected_status != "All":
    status_filter = selected_status

try:
    cases = list_agent_queue(
        api=api,
        status=status_filter,
    )
except ValueError as error:
    st.error(str(error))
    st.stop()
except Exception:
    st.error("Could not load the agent queue.")
    st.stop()

if not cases:
    st.info("No cases found in the queue.")
    st.stop()

st.caption(f"{len(cases)} case(s) shown")

for case in cases:
    with st.container(border=True):
        show_case_row(api, case)