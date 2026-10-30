from pydantic import BaseModel


class Session(BaseModel):
    user_id: str
    expires_at: int
