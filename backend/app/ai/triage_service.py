from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.ai.mock_provider import generate_mock_suggestion
from app.ai.schemas import TriageInput
from app.ai.schemas import TriageSuggestion
from app.models.case import Case
from app.models.case import CategoryEnum
from app.models.case import PriorityEnum
from app.models.user import RoleEnum
from app.models.user import User
from app.schemas.triage import TriageApplyRequest
from app.services.activity_service import log_activity
from app.services.case_service import get_case_by_id


def get_triage_suggestion(
    db: Session,
    case_id: int,
    current_user: User,
) -> TriageSuggestion:
    """
    Generate and validate a suggestion without changing the case.
    """
    if current_user.role not in {
        RoleEnum.AGENT,
        RoleEnum.ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only agents and administrators can use triage.",
        )

    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    triage_input = TriageInput(
        title=case.title,
        description=case.description,
    )

    try:
        suggestion = generate_mock_suggestion(
            triage_input,
        )

        # Explicit validation before displaying the result.
        return TriageSuggestion.model_validate(
            suggestion,
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Triage service is currently unavailable.",
        )


def apply_triage_suggestion(
    db: Session,
    case_id: int,
    current_user: User,
    suggestion: TriageSuggestion,
    apply_request: TriageApplyRequest,
) -> Case:
    """
    Apply only the fields explicitly approved by the agent.
    """
    if current_user.role not in {
        RoleEnum.AGENT,
        RoleEnum.ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only agents and administrators can "
                "apply triage."
            ),
        )

    if not any(
        [
            apply_request.apply_category,
            apply_request.apply_priority,
        ],
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The agent must approve at least "
                "one field to apply."
            ),
        )

    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    changes = []

    if apply_request.apply_category:
        old_category = case.category.value
        new_category = suggestion.category.value

        case.category = suggestion.category

        changes.append(
            f"category: {old_category} -> {new_category}"
        )

    if apply_request.apply_priority:
        old_priority = case.priority.value
        new_priority = suggestion.priority.value

        case.priority = suggestion.priority

        changes.append(
            f"priority: {old_priority} -> {new_priority}"
        )

    detail = (
        "Triage suggestion applied by agent. "
        + "; ".join(changes)
    )

    log_activity(
        db=db,
        case_id=case.id,
        actor_id=current_user.id,
        event_type="triage_suggestion_applied",
        detail=detail,
    )

    db.commit()
    db.refresh(case)

    return case