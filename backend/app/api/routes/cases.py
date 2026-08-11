from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models.user import RoleEnum, User
from app.schemas.case import (
    CaseCreate,
    CaseListResponse,
    CaseResponse,
)
from app.services.case_service import create_case
from app.services.case_service import get_case_for_user
from app.services.case_service import list_cases_for_user


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
    """
    Only requesters can create cases.
    """
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
    page: int = Query(
        default=1,
        ge=1,
    ),
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
    """
    Requesters see their own cases.
    Agents and administrators see all current cases for now.
    """
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
    """
    View one case with record-level permission checking.
    """
    return get_case_for_user(
        db=db,
        case_id=case_id,
        current_user=current_user,
    )