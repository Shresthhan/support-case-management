from pydantic import BaseModel, Field

from app.models.case import CategoryEnum, PriorityEnum


class TriageSuggestionResponse(BaseModel):
    category: CategoryEnum
    priority: PriorityEnum

    short_summary: str = Field(
        min_length=1,
        max_length=500,
    )

    recommended_next_step: str = Field(
        min_length=1,
        max_length=1000,
    )


class TriageApplyRequest(BaseModel):
    apply_category: bool = True
    apply_priority: bool = True
    apply_summary: bool = False