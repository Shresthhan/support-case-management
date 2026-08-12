from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import RoleEnum, User
from app.schemas.user import UserCreate, UserUpdate


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User:
    user = db.query(User).filter(
        User.id == user_id,
    ).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    return user


def list_all_users(
    db: Session,
) -> list[User]:
    return (
        db.query(User)
        .order_by(User.created_at.desc())
        .all()
    )


def create_user(
    db: Session,
    payload: UserCreate,
) -> User:
    existing_user = db.query(User).filter(
        User.email == payload.email,
    ).first()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists.",
        )

    if len(payload.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 8 characters.",
        )

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def update_user(
    db: Session,
    user_id: int,
    payload: UserUpdate,
) -> User:
    user = get_user_by_id(
        db=db,
        user_id=user_id,
    )

    if payload.role is not None:
        user.role = payload.role

    if payload.is_active is not None:
        user.is_active = payload.is_active

    db.commit()
    db.refresh(user)

    return user


def deactivate_user(
    db: Session,
    user_id: int,
    current_admin: User,
) -> User:
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An administrator cannot deactivate their own account.",
        )

    user = get_user_by_id(
        db=db,
        user_id=user_id,
    )

    user.is_active = False

    db.commit()
    db.refresh(user)

    return user