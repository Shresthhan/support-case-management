from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models.user import User


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    """
    Find a user by email and verify their password.

    Returns the user if authentication succeeds.
    Returns None if authentication fails.
    """
    user = db.query(User).filter(
        User.email == email,
    ).first()

    if user is None:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    if not user.is_active:
        return None

    return user