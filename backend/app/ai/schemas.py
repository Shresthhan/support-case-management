from pydantic import BaseModel


class TriageResult(BaseModel):
    priority: str
    summary: str | None = None
