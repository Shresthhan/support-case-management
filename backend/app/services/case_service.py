from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.case import Case, StatusEnum
from app.models.user import RoleEnum, User
from app.core.time import utc_now
from app.schemas.case import CaseCreate, CaseUpdate
from app.services.activity_service import log_activity


def normalize_datetime(
    value: datetime | None,
) -> datetime | None:
    """
    Store timezone-aware values as naive UTC values.
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
    current_time = utc_now()
    due_date = normalize_datetime(payload.due_date)

    if due_date is not None and due_date < current_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Due date cannot be earlier than case creation time.",
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

    db.commit()
    db.refresh(case)

    return case


def get_case_by_id(
    db: Session,
    case_id: int,
) -> Case:
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
    Requesters can only view their own cases.
    Agents and admins can view cases.
    """
    if (
        current_user.role == RoleEnum.REQUESTER
        and case.requester_id != current_user.id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You cannot access this case.",
        )


def get_case_for_user(
    db: Session,
    case_id: int,
    current_user: User,
) -> Case:
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

    if current_user.role == RoleEnum.REQUESTER:
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


def list_agent_cases(
    db: Session,
    agent: User,
    page: int = 1,
    page_size: int = 20,
    status_filter: StatusEnum | None = None,
) -> tuple[list[Case], int]:
    """
    Agents can see:
    - cases assigned to themselves
    - cases that are not assigned to anyone
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

    query = db.query(Case).filter(
        (Case.agent_id == agent.id)
        | (Case.agent_id.is_(None))
    )

    if status_filter is not None:
        query = query.filter(
            Case.status == status_filter,
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


def claim_case(
    db: Session,
    case_id: int,
    agent: User,
) -> Case:
    """
    Assign an unassigned case to the current agent.
    """
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    if case.agent_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This case is already assigned to an agent.",
        )

    if case.status in {
        StatusEnum.RESOLVED,
        StatusEnum.CLOSED,
    }:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resolved or closed cases cannot be claimed.",
        )

    case.agent_id = agent.id

    log_activity(
        db=db,
        case_id=case.id,
        actor_id=agent.id,
        event_type="case_assigned",
        detail=f"Case claimed by agent {agent.email}.",
    )

    db.commit()
    db.refresh(case)

    return case


def validate_status_change(
    current_status: StatusEnum,
    new_status: StatusEnum,
) -> None:
    """
    Define the allowed workflow transitions.
    """
    allowed_transitions = {
        StatusEnum.OPEN: {
            StatusEnum.IN_PROGRESS,
            StatusEnum.WAITING_FOR_REQUESTER,
            StatusEnum.RESOLVED,
        },
        StatusEnum.IN_PROGRESS: {
            StatusEnum.WAITING_FOR_REQUESTER,
            StatusEnum.RESOLVED,
            StatusEnum.OPEN,
        },
        StatusEnum.WAITING_FOR_REQUESTER: {
            StatusEnum.IN_PROGRESS,
            StatusEnum.RESOLVED,
            StatusEnum.OPEN,
        },
        StatusEnum.RESOLVED: {
            StatusEnum.CLOSED,
            StatusEnum.OPEN,
        },
        StatusEnum.CLOSED: set(),
    }

    if new_status == current_status:
        return

    if new_status not in allowed_transitions[current_status]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot change status from "
                f"{current_status.value} to "
                f"{new_status.value}."
            ),
        )


def update_case(
    db: Session,
    case_id: int,
    current_user: User,
    payload: CaseUpdate,
) -> Case:
    """
    Update case fields and create history entries.
    """
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    if current_user.role == RoleEnum.AGENT:
        if case.agent_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can update only cases assigned to you.",
            )

    if current_user.role == RoleEnum.REQUESTER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requesters cannot update case management fields.",
        )

    if payload.due_date is not None:
        due_date = normalize_datetime(payload.due_date)

        if due_date < case.created_at:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Due date cannot be earlier than case creation time.",
            )

        case.due_date = due_date

        log_activity(
            db=db,
            case_id=case.id,
            actor_id=current_user.id,
            event_type="due_date_changed",
            detail=f"Due date changed to {due_date.isoformat()}.",
        )

    if payload.category is not None:
        if payload.category != case.category:
            old_value = case.category.value
            case.category = payload.category

            log_activity(
                db=db,
                case_id=case.id,
                actor_id=current_user.id,
                event_type="category_changed",
                detail=(
                    f"Category changed from {old_value} "
                    f"to {payload.category.value}."
                ),
            )

    if payload.priority is not None:
        if payload.priority != case.priority:
            old_value = case.priority.value
            case.priority = payload.priority

            log_activity(
                db=db,
                case_id=case.id,
                actor_id=current_user.id,
                event_type="priority_changed",
                detail=(
                    f"Priority changed from {old_value} "
                    f"to {payload.priority.value}."
                ),
            )

    if payload.status is not None:
        validate_status_change(
            current_status=case.status,
            new_status=payload.status,
        )

        if payload.status != case.status:
            old_value = case.status.value
            case.status = payload.status

            log_activity(
                db=db,
                case_id=case.id,
                actor_id=current_user.id,
                event_type="status_changed",
                detail=(
                    f"Status changed from {old_value} "
                    f"to {payload.status.value}."
                ),
            )

    if payload.resolution_summary is not None:
        case.resolution_summary = payload.resolution_summary

    if case.status == StatusEnum.RESOLVED:
        if not case.resolution_summary or not case.resolution_summary.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A resolution summary is required.",
            )

        if case.resolved_at is None:
            case.resolved_at = utc_now()

            log_activity(
                db=db,
                case_id=case.id,
                actor_id=current_user.id,
                event_type="case_resolved",
                detail=(
                    f"Resolution: "
                    f"{case.resolution_summary}"
                ),
            )

    db.commit()
    db.refresh(case)

    return case


def reopen_case(
    db: Session,
    case_id: int,
    requester: User,
    reason: str,
) -> Case:
    """
    Requesters may reopen a recently resolved case within seven days.
    """
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    if case.requester_id != requester.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can reopen only your own cases.",
        )

    if case.status == StatusEnum.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Closed cases cannot be reopened by requesters.",
        )

    if case.status != StatusEnum.RESOLVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only resolved cases can be reopened.",
        )

    if not reason.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A reopen reason is required.",
        )

    if case.resolved_at is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This case has no resolution date.",
        )

    seven_days_after_resolution = case.resolved_at + timedelta(
        days=7,
    )

    if utc_now() > seven_days_after_resolution:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "The seven-day reopen period "
                "has expired."
            ),
        )

    old_status = case.status.value
    case.status = StatusEnum.OPEN
    case.resolved_at = None
    case.resolution_summary = None

    log_activity(
        db=db,
        case_id=case.id,
        actor_id=requester.id,
        event_type="case_reopened",
        detail=(
            f"Status changed from {old_status} to Open. "
            f"Reason: {reason.strip()}"
        ),
    )

    db.commit()
    db.refresh(case)

    return case

def reassign_case(
    db: Session,
    case_id: int,
    new_agent_id: int,
    admin: User,
) -> Case:
    """
    Reassign a case to another active agent.
    """
    case = get_case_by_id(
        db=db,
        case_id=case_id,
    )

    new_agent = db.query(User).filter(
        User.id == new_agent_id,
    ).first()

    if new_agent is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="The selected user does not exist.",
        )

    if new_agent.role != RoleEnum.AGENT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cases can only be assigned to agents.",
        )

    if not new_agent.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cases cannot be assigned to an inactive agent.",
        )

    old_agent_id = case.agent_id
    case.agent_id = new_agent.id

    log_activity(
        db=db,
        case_id=case.id,
        actor_id=admin.id,
        event_type="case_reassigned",
        detail=(
            f"Assignment changed from agent ID "
            f"{old_agent_id} to agent ID {new_agent.id}."
        ),
    )

    db.commit()
    db.refresh(case)

    return case

def get_case_counts(
    db: Session,
) -> dict[str, int]:
    """
    Return simple administrator dashboard counts.
    """
    current_time = utc_now()

    open_count = db.query(Case).filter(
        Case.status.in_(
            {
                StatusEnum.OPEN,
                StatusEnum.IN_PROGRESS,
                StatusEnum.WAITING_FOR_REQUESTER,
            },
        ),
    ).count()

    overdue_count = db.query(Case).filter(
        Case.due_date.is_not(None),
        Case.due_date < current_time,
        ~Case.status.in_(
            {
                StatusEnum.RESOLVED,
                StatusEnum.CLOSED,
            },
        ),
    ).count()

    resolved_count = db.query(Case).filter(
        Case.status == StatusEnum.RESOLVED,
    ).count()

    return {
        "open": open_count,
        "overdue": overdue_count,
        "resolved": resolved_count,
    }