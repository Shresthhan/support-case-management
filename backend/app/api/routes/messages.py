from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models.user import RoleEnum, User
from app.schemas.message import MessageCreate, MessageResponse
from app.services.message_service import add_internal_note
from app.services.message_service import add_public_reply
from app.services.message_service import list_messages_for_user


router = APIRouter(
    prefix="/cases/{case_id}/messages",
    tags=["Messages"],
)


@router.post(
    "/reply",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_public_reply(
    case_id: int,
    payload: MessageCreate,
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
    Add a public message visible to the requester.
    """
    return add_public_reply(
        db=db,
        case_id=case_id,
        author=current_user,
        payload=payload,
    )


@router.post(
    "/note",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_internal_note(
    case_id: int,
    payload: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            RoleEnum.AGENT,
            RoleEnum.ADMIN,
        ),
    ),
):
    """
    Add an internal note visible only to agents and administrators.
    """
    return add_internal_note(
        db=db,
        case_id=case_id,
        author=current_user,
        payload=payload,
    )


@router.get(
    "",
    response_model=list[MessageResponse],
)
def get_case_messages(
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
    Return messages visible to the current user.
    """
    return list_messages_for_user(
        db=db,
        case_id=case_id,
        current_user=current_user,
    )