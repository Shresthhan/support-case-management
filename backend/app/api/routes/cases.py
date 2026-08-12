from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models.case import StatusEnum
from app.models.user import RoleEnum, User
from app.schemas.case import (
    CaseCreate,
    CaseListResponse,
    CaseResponse,
    CaseUpdate,
)
from app.services.case_service import claim_case
from app.services.case_service import create_case
from app.services.case_service import get_case_for_user
from app.services.case_service import list_agent_cases
from app.services.case_service import list_cases_for_user
from app.services.case_service import reopen_case
from app.services.case_service import update_case


router = APIRouter(
    prefix="/cases",
    tags=["Cases"],
)


@router.post(
    "",
    response_model=CaseResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_new_case(
    payload: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleEnum.REQUESTER),
    ),
):
    return create_case(
        db=db,
        requester=current_user,
        payload=payload,
    )


@router.get(
    "",
    response_model=CaseListResponse,
)
def list_cases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            RoleEnum.REQUESTER,
            RoleEnum.AGENT,
            RoleEnum.ADMIN,
        ),
    ),
):
    cases, total = list_cases_for_user(
        db=db,
        current_user=current_user,
        page=page,
        page_size=page_size,
    )

    return CaseListResponse(
        items=cases,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/agent-queue",
    response_model=CaseListResponse,
)
def get_agent_queue(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    status_filter: StatusEnum | None = Query(
        default=None,
        alias="status",
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleEnum.AGENT),
    ),
):
    cases, total = list_agent_cases(
        db=db,
        agent=current_user,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )

    return CaseListResponse(
        items=cases,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{case_id}",
    response_model=CaseResponse,
)
def get_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            RoleEnum.REQUESTER,
            RoleEnum.AGENT,
            RoleEnum.ADMIN,
        ),
    ),
):
    return get_case_for_user(
        db=db,
        case_id=case_id,
        current_user=current_user,
    )


@router.post(
    "/{case_id}/claim",
    response_model=CaseResponse,
)
def claim_unassigned_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleEnum.AGENT),
    ),
):
    return claim_case(
        db=db,
        case_id=case_id,
        agent=current_user,
    )


@router.patch(
    "/{case_id}",
    response_model=CaseResponse,
)
def update_existing_case(
    case_id: int,
    payload: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            RoleEnum.AGENT,
            RoleEnum.ADMIN,
        ),
    ),
):
    return update_case(
        db=db,
        case_id=case_id,
        current_user=current_user,
        payload=payload,
    )


@router.post(
    "/{case_id}/reopen",
    response_model=CaseResponse,
)
def reopen_resolved_case(
    case_id: int,
    reason: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(RoleEnum.REQUESTER),
    ),
):
    return reopen_case(
        db=db,
        case_id=case_id,
        requester=current_user,
        reason=reason,
    )