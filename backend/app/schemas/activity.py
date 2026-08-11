from pydantic import BaseModel


class ActivityBase(BaseModel):
    action: str
