import streamlit as st

from api_client.agent_api import update_case
from api_client.cases_api import get_case
from api_client.cases_api import list_cases
from api_client.cases_api import reopen_case
from api_client.client import ApiClient
from api_client.messages_api import add_internal_note
from api_client.messages_api import add_public_reply
from api_client.messages_api import list_messages


st.set_page_config(
    page_title="Case Detail",
    page_icon="📄",
    layout="wide",
)

def show_agent_update_form(
    api: ApiClient,
    case: dict,
) -> None:
    user = st.session_state.user
    role = str(user.get("role", "")).lower()

    if role not in {"agent", "admin"}:
        return

    case_id = case["id"]

    st.subheader("Update case")

    category_options = [
        "Technical",
        "Account",
        "Billing",
        "Other",
    ]

    priority_options = [
        "Low",
        "Medium",
        "High",
        "Urgent",
    ]

    status_options = [
        "Open",
        "In Progress",
        "Waiting for Requester",
        "Resolved",
        "Closed",
    ]

    current_category = case.get(
        "category",
        "Other",
    )

    current_priority = case.get(
        "priority",
        "Medium",
    )

    current_status = case.get(
        "status",
        "Open",
    )

    if current_category not in category_options:
        current_category = "Other"

    if current_priority not in priority_options:
        current_priority = "Medium"

    if current_status not in status_options:
        current_status = "Open"

    with st.form(
        f"update_case_form_{case_id}",
    ):
        category = st.selectbox(
            "Category",
            options=category_options,
            index=category_options.index(
                current_category,
            ),
        )

        priority = st.selectbox(
            "Priority",
            options=priority_options,
            index=priority_options.index(
                current_priority,
            ),
        )

        status = st.selectbox(
            "Status",
            options=status_options,
            index=status_options.index(
                current_status,
            ),
        )

        resolution_summary = st.text_area(
            "Resolution summary",
            value=case.get(
                "resolution_summary",
                "",
            ) or "",
            max_chars=5000,
        )

        submitted = st.form_submit_button(
            "Save case changes",
            use_container_width=True,
        )

    if not submitted:
        return

    payload = {
        "category": category,
        "priority": priority,
        "status": status,
        "resolution_summary": (
            resolution_summary.strip()
            or None
        ),
    }

    try:
        update_case(
            api=api,
            case_id=case_id,
            payload=payload,
        )

        st.success("Case updated successfully.")
        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Could not update the case."
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


def format_value(value) -> str:
    if value is None:
        return "—"

    return str(value)


def show_case_summary(case: dict) -> None:
    st.subheader(
        f"{case.get('case_number', 'Case')} "
        f"— {case.get('title', '')}"
    )

    left, right = st.columns(2)

    with left:
        st.write(
            f"**Status:** "
            f"{format_value(case.get('status'))}"
        )

        st.write(
            f"**Priority:** "
            f"{format_value(case.get('priority'))}"
        )

        st.write(
            f"**Category:** "
            f"{format_value(case.get('category'))}"
        )

        st.write(
            f"**Requester ID:** "
            f"{format_value(case.get('requester_id'))}"
        )

    with right:
        st.write(
            f"**Agent ID:** "
            f"{format_value(case.get('agent_id'))}"
        )

        st.write(
            f"**Created:** "
            f"{format_value(case.get('created_at'))}"
        )

        st.write(
            f"**Updated:** "
            f"{format_value(case.get('updated_at'))}"
        )

        st.write(
            f"**Due date:** "
            f"{format_value(case.get('due_date'))}"
        )

    st.write("### Description")
    st.write(
        format_value(case.get("description")),
    )

    resolution = case.get("resolution_summary")

    if resolution:
        st.write("### Resolution")
        st.write(resolution)


def show_messages(
    api: ApiClient,
    case_id: int,
) -> None:
    st.subheader("Conversation")

    try:
        messages = list_messages(
            api=api,
            case_id=case_id,
        )

    except ValueError as error:
        st.error(str(error))
        return

    if not messages:
        st.info("There are no messages yet.")
        return

    for message in messages:
        is_internal = message.get(
            "is_internal",
            False,
        )

        if is_internal:
            label = "Internal note"
        else:
            label = "Public reply"

        created_at = format_value(
            message.get("created_at"),
        )

        with st.chat_message(
            "assistant" if is_internal else "user",
        ):
            st.caption(
                f"{label} · "
                f"Author ID: {message.get('author_id')} · "
                f"{created_at}"
            )

            st.write(
                message.get("body", ""),
            )


def show_public_reply_form(
    api: ApiClient,
    case_id: int,
) -> None:
    st.subheader("Add a public reply")

    with st.form(
        f"public_reply_form_{case_id}",
    ):
        body = st.text_area(
            "Message",
            placeholder=(
                "Write a message visible to the "
                "requester and support team."
            ),
            max_chars=5000,
        )

        submitted = st.form_submit_button(
            "Send public reply",
            use_container_width=True,
        )

    if not submitted:
        return

    if not body.strip():
        st.error("Message cannot be empty.")
        return

    try:
        add_public_reply(
            api=api,
            case_id=case_id,
            body=body.strip(),
        )

        st.success("Public reply added.")
        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Could not send the public reply."
        )


def show_internal_note_form(
    api: ApiClient,
    case_id: int,
) -> None:
    user = st.session_state.user
    role = str(user.get("role", "")).lower()

    if role not in {"agent", "admin"}:
        return

    st.subheader("Add an internal note")

    with st.form(
        f"internal_note_form_{case_id}",
    ):
        body = st.text_area(
            "Internal note",
            placeholder=(
                "This note is visible only to "
                "agents and administrators."
            ),
            max_chars=5000,
        )

        submitted = st.form_submit_button(
            "Add internal note",
            use_container_width=True,
        )

    if not submitted:
        return

    if not body.strip():
        st.error("Internal note cannot be empty.")
        return

    try:
        add_internal_note(
            api=api,
            case_id=case_id,
            body=body.strip(),
        )

        st.success("Internal note added.")
        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Could not add the internal note."
        )


def show_reopen_form(
    api: ApiClient,
    case: dict,
) -> None:
    user = st.session_state.user
    role = str(user.get("role", "")).lower()

    if role != "requester":
        return

    status_value = str(
        case.get("status", "")
    ).lower()

    if status_value not in {
        "resolved",
        "closed",
    }:
        return

    case_id = case["id"]

    st.subheader("Reopen case")

    with st.form(
        f"reopen_form_{case_id}",
    ):
        reason = st.text_area(
            "Why are you reopening this case?",
            max_chars=5000,
        )

        submitted = st.form_submit_button(
            "Reopen case",
            use_container_width=True,
        )

    if not submitted:
        return

    if not reason.strip():
        st.error("A reopening reason is required.")
        return

    try:
        reopen_case(
            api=api,
            case_id=case_id,
            reason=reason.strip(),
        )

        st.success("Case reopened.")
        st.rerun()

    except ValueError as error:
        st.error(str(error))

    except Exception:
        st.error(
            "Could not reopen the case."
        )


require_login()

st.title("Case Detail")

api = create_api_client()

try:
    cases = list_cases(api)

except ValueError as error:
    st.error(str(error))
    st.stop()

except Exception:
    st.error(
        "Could not load cases from the API."
    )
    st.stop()

if not cases:
    st.info(
        "You do not have any cases to view."
    )
    st.stop()

case_options = {}

for case in cases:
    case_id = case.get("id")
    case_number = case.get(
        "case_number",
        f"Case {case_id}",
    )
    title = case.get("title", "")

    case_options[
        f"{case_number} — {title}"
    ] = case_id

selected_label = st.selectbox(
    "Select a case",
    options=list(case_options.keys()),
)

selected_case_id = case_options[selected_label]

try:
    case = get_case(
        api=api,
        case_id=selected_case_id,
    )

except ValueError as error:
    st.error(str(error))
    st.stop()

except Exception:
    st.error(
        "Could not load the selected case."
    )
    st.stop()

show_case_summary(case)

show_agent_update_form(
    api=api,
    case=case,
)

st.divider()

show_messages(
    api=api,
    case_id=selected_case_id,
)

st.divider()

show_public_reply_form(
    api=api,
    case_id=selected_case_id,
)

show_internal_note_form(
    api=api,
    case_id=selected_case_id,
)

show_reopen_form(
    api=api,
    case=case,
)