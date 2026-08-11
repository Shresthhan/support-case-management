from pydantic import BaseModel


class MessageBase(BaseModel):
    body: str
