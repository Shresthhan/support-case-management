import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Index
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.time import utc_now


class CategoryEnum(str, enum.Enum):
    TECHNICAL = "Technical"
    ACCOUNT = "Account"
    BILLING = "Billing"
    OTHER = "Other"


class PriorityEnum(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class StatusEnum(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    WAITING_FOR_REQUESTER = "Waiting for Requester"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class Case(Base):
    __tablename__ = "cases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    case_number: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        default=lambda: f"CASE-{uuid.uuid4().hex[:8].upper()}",
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    category: Mapped[CategoryEnum] = mapped_column(
        Enum(CategoryEnum),
        nullable=False,
        default=CategoryEnum.OTHER,
    )

    priority: Mapped[PriorityEnum] = mapped_column(
        Enum(PriorityEnum),
        nullable=False,
        default=PriorityEnum.MEDIUM,
    )

    status: Mapped[StatusEnum] = mapped_column(
        Enum(StatusEnum),
        nullable=False,
        default=StatusEnum.OPEN,
        index=True,
    )

    requester_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    agent_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    due_date: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    resolved_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    resolution_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    requester = relationship(
        "User",
        foreign_keys=[requester_id],
    )

    assigned_agent = relationship(
        "User",
        foreign_keys=[agent_id],
    )

    messages = relationship(
        "Message",
        back_populates="case",
        cascade="all, delete-orphan",
    )

    activities = relationship(
        "ActivityHistory",
        back_populates="case",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "ix_cases_status_agent",
            "status",
            "agent_id",
        ),
    )