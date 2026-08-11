from sqlalchemy.orm import Session

from app.models.activity_history import ActivityHistory


def log_activity(
    db: Session,
    case_id: int,
    actor_id: int,
    event_type: str,
    detail: str | None = None,
) -> ActivityHistory:
    """
    Create one activity-history record.

    The caller decides when to commit the transaction.
    """
    activity = ActivityHistory(
        case_id=case_id,
        actor_id=actor_id,
        event_type=event_type,
        detail=detail,
    )

    db.add(activity)

    return activity