from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import RoleEnum
from app.models.user import User


SEED_USERS = [
    {
        "email": "requester@example.com",
        "password": "Requester123!",
        "role": RoleEnum.REQUESTER,
    },
    {
        "email": "agent@example.com",
        "password": "Agent123!",
        "role": RoleEnum.AGENT,
    },
    {
        "email": "admin@example.com",
        "password": "Admin123!",
        "role": RoleEnum.ADMIN,
    },
]


def seed_users(db: Session) -> None:
    for seed_user in SEED_USERS:
        existing_user = db.query(User).filter(
            User.email == seed_user["email"],
        ).first()

        if existing_user is not None:
            continue

        user = User(
            email=seed_user["email"],
            hashed_password=hash_password(
                seed_user["password"],
            ),
            role=seed_user["role"],
            is_active=True,
        )

        db.add(user)

    db.commit()


def main() -> None:
    db = SessionLocal()

    try:
        seed_users(db)
        print("Seed users created successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    main()