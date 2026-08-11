from pydantic import BaseModel


class TriageRequest(BaseModel):
    message: str
