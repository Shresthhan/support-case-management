from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.ai.schemas import TriageSuggestion
from app.ai.triage_service import apply_triage_suggestion
from app.ai.triage_service import get_triage_suggestion
from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models.user import RoleEnum
from app.models.user import User
from app.schemas.case import CaseResponse
from app.schemas.triage import TriageApplyRequest
from app.schemas.triage import TriageSuggestionResponse


router = APIRouter(
    prefix="/cases/{case_id}/triage",
    tags=["AI Triage"],
)


@router.post(
    "/suggest",
    response_model=TriageSuggestionResponse,
)
def suggest_case_triage(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            RoleEnum.AGENT,
            RoleEnum.ADMIN,
        ),
    ),
):
    """
    Generate a suggestion without changing the case.
    """
    return get_triage_suggestion(
        db=db,
        case_id=case_id,
        current_user=current_user,
    )


@router.post(
    "/apply",
    response_model=CaseResponse,
)
def apply_case_triage(
    case_id: int,
    suggestion: TriageSuggestion,
    apply_request: TriageApplyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            RoleEnum.AGENT,
            RoleEnum.ADMIN,
        ),
    ),
):
    """
    Apply a suggestion only after explicit agent confirmation.
    """
    return apply_triage_suggestion(
        db=db,
        case_id=case_id,
        current_user=current_user,
        suggestion=suggestion,
        apply_request=apply_request,
    )