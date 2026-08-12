from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.core.database import get_db
from app.models.user import RoleEnum, User
from app.schemas.user import UserCreate
from app.schemas.user import UserResponse
from app.schemas.user import UserUpdate
from app.services.user_service import create_user
from app.services.user_service import deactivate_user
from app.services.user_service import list_all_users
from app.services.user_service import update_user


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "",
    response_model=list[UserResponse],
)
def get_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(RoleEnum.ADMIN),
    ),
):
    """
    List all users.

    Only administrators may use this endpoint.
    """
    return list_all_users(db=db)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def add_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(RoleEnum.ADMIN),
    ),
):
    """
    Create a new user.
    """
    return create_user(
        db=db,
        payload=payload,
    )


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def edit_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(RoleEnum.ADMIN),
    ),
):
    """
    Change a user's role or active status.
    """
    return update_user(
        db=db,
        user_id=user_id,
        payload=payload,
    )


@router.post(
    "/{user_id}/deactivate",
    response_model=UserResponse,
)
def deactivate_existing_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(
        require_roles(RoleEnum.ADMIN),
    ),
):
    """
    Deactivate a user without deleting their history.
    """
    return deactivate_user(
        db=db,
        user_id=user_id,
        current_admin=current_admin,
    )