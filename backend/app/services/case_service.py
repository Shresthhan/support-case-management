from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.case import Case, StatusEnum
from app.models.user import User
from app.schemas.case import CaseCreate
from app.services.activity_service import log_activity


def normalize_datetime(value: datetime | None) -> datetime | None:
    """
    Convert a timezone-aware datetime to a naive UTC datetime.

    The database stores UTC timestamps.
    """
    if value is None:
        return None

    if value.tzinfo is not None:
        return value.astimezone(timezone.utc).replace(
            tzinfo=None,
        )

    return value


def create_case(
    db: Session,
    requester: User,
    payload: CaseCreate,
) -> Case:
    """
    Create a new support case and its activity-history entry.
    """
    current_time = datetime.utcnow()
    due_date = normalize_datetime(payload.due_date)

    if due_date is not None and due_date < current_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Due date cannot be earlier than the case creation time.",
        )

    case = Case(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        priority=payload.priority,
        status=StatusEnum.OPEN,
        requester_id=requester.id,
        due_date=due_date,
    )

    db.add(case)

    # SQLAlchemy obtains the new case ID before commit.
    db.flush()

    log_activity(
        db=db,
        case_id=case.id,
        actor_id=requester.id,
        event_type="case_created",
        detail=(
            f"Case created with priority "
            f"{payload.priority.value}."
        ),
    )

    # Case and history are saved together.
    db.commit()

    db.refresh(case)

    return case


def get_case_by_id(
    db: Session,
    case_id: int,
) -> Case:
    """
    Find one case or return HTTP 404.
    """
    case = db.query(Case).filter(
        Case.id == case_id,
    ).first()

    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found.",
        )

    return case


def check_case_view_permission(
    case: Case,
    current_user: User,
) -> None:
    """
    Enforce record-level access.

    Requesters may view only cases they created.
    Agents and administrators can view cases according
    to their broader application permissions.
    """
    if (
        current_user.role.value == "requester"
        and case.requester_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot view this case.",
        )


def get_case_for_user(
    db: Session,
    case_id: int,
    current_user: User,
) -> Case:
    """
    Find a case and verify that the current user may view it.
    """
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    check_case_view_permission(
        case=case,
        current_user=current_user,
    )

    return case


def list_cases_for_user(
    db: Session,
    current_user: User,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Case], int]:
    """
    Return cases that the current user is allowed to see.
    """
    if page < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page must be at least 1.",
        )

    if page_size < 1 or page_size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Page size must be between 1 and 100.",
        )

    query = db.query(Case)

    if current_user.role.value == "requester":
        query = query.filter(
            Case.requester_id == current_user.id,
        )

    total = query.count()

    offset = (page - 1) * page_size

    cases = (
        query.order_by(Case.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return cases, total