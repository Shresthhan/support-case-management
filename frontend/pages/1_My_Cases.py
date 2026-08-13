import streamlit as st

from api_client.cases_api import create_case
from api_client.agent_api import list_agent_queue
from api_client.cases_api import list_cases
from api_client.client import ApiClient


st.set_page_config(
    page_title="My Cases",
    page_icon="🎫",
    layout="wide",
)


def require_login() -> None:
    if st.session_state.get("user") is None:
        st.warning("Please log in first.")
        st.stop()


def display_cases(cases: list[dict]) -> None:
    if not cases:
        st.info(
            "You do not have any cases yet.",
        )
        return

    rows = []

    for case in cases:
        rows.append(
            {
                "ID": case.get("id"),
                "Title": case.get("title"),
                "Status": case.get("status"),
                "Priority": case.get("priority"),
                "Category": case.get("category"),
                "Created": case.get("created_at"),
            }
        )

    st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
    )


def show_create_case_form(api: ApiClient) -> None:
    st.subheader("Create a new case")

    with st.form("create_case_form"):
        title = st.text_input(
            "Title",
            placeholder="Unable to access my account",
        )

        description = st.text_area(
            "Description",
            placeholder=(
                "Explain the issue in detail."
            ),
        )

        category = st.selectbox(
            "Category",
            options=[
                "Technical",
                "Account",
                "Billing",
                "Other",
            ],
        )

        priority = st.selectbox(
            "Priority",
            options=[
                "Low",
                "Medium",
                "High",
                "Urgent",
            ],
        )

        submitted = st.form_submit_button(
            "Create case",
            use_container_width=True,
        )

    if not submitted:
        return

    if not title.strip():
        st.error("Title is required.")
        return

    if not description.strip():
        st.error("Description is required.")
        return

    try:
        created_case = create_case(
            api=api,
            title=title.strip(),
            description=description.strip(),
            category=category,
            priority=priority,
        )

        st.success(
            "Case created successfully. "
            f"Case ID: {created_case.get('id')}"
        )

        st.cache_data.clear()
        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Could not connect to the API."
        )


require_login()

st.title("My Cases")

api = ApiClient(
    base_url=st.session_state.api_base_url,
    token=st.session_state.token,
)

st.subheader("Your cases")

try:
    user = st.session_state.user
    role = str(user.get("role", "")).lower()

    if role == "agent":
        cases = list_agent_queue(api)
    else:
        cases = list_cases(api)
    display_cases(cases)

except ValueError as error:
    st.error(str(error))

except Exception:
    st.error(
        "Could not load cases from the API."
    )

st.divider()

show_create_case_form(api)