from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.case import (
    CategoryEnum,
    PriorityEnum,
    StatusEnum,
)


class CaseCreate(BaseModel):
    title: str = Field(
        min_length=3,
        max_length=255,
    )

    description: str = Field(
        min_length=1,
    )

    category: CategoryEnum = CategoryEnum.OTHER
    priority: PriorityEnum = PriorityEnum.MEDIUM
    due_date: datetime | None = None


class CaseUpdate(BaseModel):
    category: CategoryEnum | None = None
    priority: PriorityEnum | None = None
    status: StatusEnum | None = None
    due_date: datetime | None = None
    agent_id: int | None = None
    resolution_summary: str | None = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: str
    title: str
    description: str
    category: CategoryEnum
    priority: PriorityEnum
    status: StatusEnum
    requester_id: int
    agent_id: int | None
    created_at: datetime
    updated_at: datetime
    due_date: datetime | None
    resolved_at: datetime | None
    resolution_summary: str | None


class CaseListResponse(BaseModel):
    items: list[CaseResponse]
    total: int
    page: int
    page_size: int