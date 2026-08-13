import streamlit as st

from api_client.admin_api import get_case_summary
from api_client.cases_api import list_cases
from api_client.client import ApiClient
from api_client.users_api import create_user
from api_client.users_api import list_active_agents
from api_client.users_api import list_users
from api_client.users_api import update_user


st.set_page_config(
    page_title="Admin Dashboard",
    page_icon="📊",
    layout="wide",
)


def require_admin() -> None:
    user = st.session_state.get("user")

    if user is None:
        st.warning("Please log in first.")
        st.stop()

    role = str(
        user.get("role", "")
    ).lower()

    if role != "admin":
        st.error(
            "You do not have permission to view "
            "this page."
        )
        st.stop()


def create_api_client() -> ApiClient:
    return ApiClient(
        base_url=st.session_state.api_base_url,
        token=st.session_state.token,
    )


def get_count(
    summary: dict,
    *keys: str,
) -> int:
    for key in keys:
        value = summary.get(key)

        if isinstance(value, int):
            return value

    return 0


def build_case_label(case: dict) -> str:
    return (
        f"{case.get('case_number', 'Case')} "
        f"— {case.get('title', '')}"
    )


def build_agent_label(user: dict) -> str:
    return (
        f"{user.get('email', 'Unknown')} "
        f"(ID {user.get('id')})"
    )


def build_user_label(user: dict) -> str:
    return (
        f"{user.get('email', 'Unknown')} "
        f"(ID {user.get('id')})"
    )


def assign_case_to_agent(
    api: ApiClient,
    case_id: int,
    agent_id: int,
) -> dict:
    response = api.patch(
        f"/cases/{case_id}/assignment",
        json={
            "agent_id": agent_id,
        },
    )

    if response.status_code not in (200, 201):
        raise ValueError(
            api.error_message(response),
        )

    return response.json()


def show_create_user_form(
    api: ApiClient,
) -> None:
    st.subheader("Create a new user")

    with st.form("create_user_form"):
        new_email = st.text_input(
            "Email",
            placeholder="new.agent@example.com",
        )

        new_password = st.text_input(
            "Temporary password",
            type="password",
            help=(
                "Give this password to the user "
                "securely."
            ),
        )

        new_role = st.selectbox(
            "Role",
            options=[
                "requester",
                "agent",
                "admin",
            ],
        )

        submitted = st.form_submit_button(
            "Create user",
            use_container_width=True,
        )

    if not submitted:
        return

    email = new_email.strip()
    password = new_password

    if not email:
        st.error("Email is required.")
        return

    if "@" not in email:
        st.error(
            "Please enter a valid email address."
        )
        return

    if not password:
        st.error("Password is required.")
        return

    if len(password) < 8:
        st.error(
            "Password must contain at least "
            "8 characters."
        )
        return

    try:
        create_user(
            api=api,
            email=email,
            password=password,
            role=new_role,
        )

        st.success(
            "User created successfully."
        )
        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Could not create the user."
        )


def show_user_table(
    users: list[dict],
) -> None:
    if not users:
        st.info("No users found.")
        return

    user_rows = []

    for user in users:
        user_rows.append(
            {
                "ID": user.get("id"),
                "Email": user.get("email"),
                "Role": user.get("role"),
                "Active": user.get("is_active"),
                "Created At": user.get("created_at"),
            }
        )

    st.dataframe(
        user_rows,
        use_container_width=True,
        hide_index=True,
    )


def show_user_edit_form(
    api: ApiClient,
    users: list[dict],
) -> None:
    if not users:
        return

    st.divider()
    st.subheader("Change user status or role")

    user_map = {
        build_user_label(user): user
        for user in users
    }

    selected_label = st.selectbox(
        "Select user",
        options=list(user_map.keys()),
        key="admin_selected_user",
    )

    selected_user = user_map[selected_label]

    role_options = [
        "requester",
        "agent",
        "admin",
    ]

    current_role = str(
        selected_user.get(
            "role",
            "requester",
        )
    ).lower()

    if current_role not in role_options:
        current_role = "requester"

    with st.form("edit_user_form"):
        selected_role = st.selectbox(
            "Role",
            options=role_options,
            index=role_options.index(
                current_role,
            ),
        )

        selected_active = st.checkbox(
            "Account is active",
            value=bool(
                selected_user.get(
                    "is_active",
                    False,
                )
            ),
        )

        submitted = st.form_submit_button(
            "Save user changes",
            use_container_width=True,
        )

    if not submitted:
        return

    try:
        update_user(
            api=api,
            user_id=selected_user["id"],
            payload={
                "role": selected_role,
                "is_active": selected_active,
            },
        )

        st.success(
            "User updated successfully."
        )
        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Could not update the user."
        )


def show_case_management(
    api: ApiClient,
) -> None:
    st.subheader("Case management")

    try:
        cases = list_cases(api)
        agents = list_active_agents(api)

    except ValueError as error:
        st.error(str(error))
        return

    except Exception:
        st.error(
            "Could not load cases or agents."
        )
        return

    if not cases:
        st.info("No cases found.")
        return

    status_options = [
        "Open",
        "In Progress",
        "Waiting for Requester",
        "Resolved",
        "Closed",
    ]

    priority_options = [
        "Low",
        "Medium",
        "High",
        "Urgent",
    ]

    filter_col1, filter_col2 = st.columns(2)

    with filter_col1:
        selected_status = st.selectbox(
            "Filter by status",
            options=["All"] + status_options,
            key="admin_status_filter",
        )

    with filter_col2:
        selected_priority = st.selectbox(
            "Filter by priority",
            options=["All"] + priority_options,
            key="admin_priority_filter",
        )

    filtered_cases = cases

    if selected_status != "All":
        filtered_cases = [
            case
            for case in filtered_cases
            if case.get("status")
            == selected_status
        ]

    if selected_priority != "All":
        filtered_cases = [
            case
            for case in filtered_cases
            if case.get("priority")
            == selected_priority
        ]

    st.caption(
        f"{len(filtered_cases)} case(s) found"
    )

    if not filtered_cases:
        st.info(
            "No cases match the selected filters."
        )
        return

    case_rows = []

    for case in filtered_cases:
        case_rows.append(
            {
                "ID": case.get("id"),
                "Case Number": case.get(
                    "case_number",
                ),
                "Title": case.get("title"),
                "Status": case.get("status"),
                "Priority": case.get("priority"),
                "Category": case.get("category"),
                "Requester ID": case.get(
                    "requester_id",
                ),
                "Agent ID": case.get("agent_id"),
                "Created": case.get("created_at"),
            }
        )

    st.dataframe(
        case_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.divider()

    st.subheader("Assign or reassign a case")

    if not agents:
        st.warning(
            "There are no active agents available."
        )
        return

    case_map = {
        build_case_label(case): case
        for case in filtered_cases
    }

    agent_map = {
        build_agent_label(agent): agent["id"]
        for agent in agents
    }

    with st.form(
        "case_management_assignment_form",
    ):
        selected_case_label = st.selectbox(
            "Select case",
            options=list(case_map.keys()),
            key="admin_management_case",
        )

        selected_case = case_map[
            selected_case_label
        ]

        current_agent_id = selected_case.get(
            "agent_id",
        )

        if current_agent_id is None:
            st.info(
                "This case is currently unassigned."
            )
        else:
            st.caption(
                f"Current agent ID: "
                f"{current_agent_id}"
            )

        selected_agent_label = st.selectbox(
            "Assign to active agent",
            options=list(agent_map.keys()),
            key="admin_management_agent",
        )

        submitted = st.form_submit_button(
            "Save assignment",
            use_container_width=True,
        )

    if not submitted:
        return

    selected_agent_id = agent_map[
        selected_agent_label
    ]

    try:
        assign_case_to_agent(
            api=api,
            case_id=selected_case["id"],
            agent_id=selected_agent_id,
        )

        st.success(
            "Case assignment saved successfully."
        )
        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Could not save the case assignment."
        )


require_admin()

st.title("Admin Dashboard")

st.caption(
    "Overview of support case activity "
    "and administration tools."
)

api = create_api_client()

(
    tab_overview,
    tab_users,
    tab_case_management,
) = st.tabs(
    [
        "Overview",
        "Users",
        "Case Management",
    ]
)


with tab_overview:
    try:
        summary = get_case_summary(api)

    except ValueError as error:
        st.error(str(error))
        st.stop()

    except Exception:
        st.error(
            "Could not load the admin summary."
        )
        st.stop()

    if not isinstance(summary, dict):
        st.error(
            "The API returned an unexpected "
            "summary format."
        )
        st.stop()

    st.subheader("Case overview")

    total = get_count(
        summary,
        "total",
        "total_cases",
        "all",
    )

    open_count = get_count(
        summary,
        "open",
        "open_cases",
    )

    in_progress = get_count(
        summary,
        "in_progress",
        "in_progress_cases",
    )

    waiting = get_count(
        summary,
        "waiting_for_requester",
        "waiting_for_requester_cases",
    )

    resolved = get_count(
        summary,
        "resolved",
        "resolved_cases",
    )

    closed = get_count(
        summary,
        "closed",
        "closed_cases",
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total cases",
            total,
        )

    with col2:
        st.metric(
            "Open cases",
            open_count,
        )

    with col3:
        st.metric(
            "In progress",
            in_progress,
        )

    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            "Waiting for requester",
            waiting,
        )

    with col5:
        st.metric(
            "Resolved",
            resolved,
        )

    with col6:
        st.metric(
            "Closed",
            closed,
        )

    st.divider()

    st.subheader("Raw summary response")
    st.json(summary)


with tab_users:
    st.subheader("User management")

    show_create_user_form(api)

    st.divider()

    try:
        users = list_users(api)

    except ValueError as error:
        st.error(str(error))
        st.stop()

    except Exception:
        st.error(
            "Could not load users."
        )
        st.stop()

    show_user_table(users)

    show_user_edit_form(
        api=api,
        users=users,
    )


with tab_case_management:
    show_case_management(api)