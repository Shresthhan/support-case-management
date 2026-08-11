from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from app.core.security import get_current_user
from app.models.user import RoleEnum, User


class RoleChecker:
    """
    Reusable role-based access checker.

    Example:

    current_user: User = Depends(
        RoleChecker([RoleEnum.ADMIN])
    )
    """

    def __init__(self, allowed_roles: list[RoleEnum]):
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission for this action.",
            )

        return current_user


def require_roles(
    *roles: RoleEnum,
) -> Callable:
    """
    Helper function for declaring allowed roles.
    """
    return RoleChecker(list(roles))