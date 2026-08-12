from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.message import Message
from app.models.user import RoleEnum, User
from app.schemas.message import MessageCreate
from app.services.activity_service import log_activity
from app.services.case_service import check_case_view_permission
from app.services.case_service import get_case_by_id


def add_public_reply(
    db: Session,
    case_id: int,
    author: User,
    payload: MessageCreate,
) -> Message:
    """
    Add a public message visible to the requester.
    """
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    check_case_view_permission(
        case=case,
        current_user=author,
    )

    message = Message(
        case_id=case.id,
        author_id=author.id,
        body=payload.body,
        is_internal=False,
    )

    db.add(message)
    db.flush()

    log_activity(
        db=db,
        case_id=case.id,
        actor_id=author.id,
        event_type="public_reply_added",
        detail="A public reply was added.",
    )

    db.commit()
    db.refresh(message)

    return message


def add_internal_note(
    db: Session,
    case_id: int,
    author: User,
    payload: MessageCreate,
) -> Message:
    """
    Add an internal note visible only to agents and administrators.
    """
    if author.role not in {
        RoleEnum.AGENT,
        RoleEnum.ADMIN,
    }:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Only agents and administrators can "
                "add internal notes."
            ),
        )

    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    message = Message(
        case_id=case.id,
        author_id=author.id,
        body=payload.body,
        is_internal=True,
    )

    db.add(message)
    db.flush()

    log_activity(
        db=db,
        case_id=case.id,
        actor_id=author.id,
        event_type="internal_note_added",
        detail="An internal note was added.",
    )

    db.commit()
    db.refresh(message)

    return message


def list_messages_for_user(
    db: Session,
    case_id: int,
    current_user: User,
) -> list[Message]:
    """
    Return only messages visible to the current user.
    """
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    check_case_view_permission(
        case=case,
        current_user=current_user,
    )

    query = db.query(Message).filter(
        Message.case_id == case_id,
    )

    if current_user.role == RoleEnum.REQUESTER:
        query = query.filter(
            Message.is_internal.is_(False),
        )

    return query.order_by(
        Message.created_at.asc(),
    ).all()