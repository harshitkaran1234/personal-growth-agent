from typing import Optional

from pydantic import BaseModel, field_validator

from personal_growth_agent.database.model import User, Weekday
from personal_growth_agent.schema.validators import validate_hh_mm


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    reminder_time: str
    review_day: Weekday
    is_onboarded: bool
    created_at: Optional[int]

    @classmethod
    def from_user(cls, user: User) -> "UserResponse":
        return cls(id=str(user.id), **user.model_dump(exclude={"last_login_at", "updated_at"}))


class UpdateUserRequest(BaseModel):
    name: Optional[str] = None
    reminder_time: Optional[str] = None
    review_day: Optional[Weekday] = None
    is_onboarded: Optional[bool] = None

    @field_validator("reminder_time")
    @classmethod
    def check_reminder_time(cls, value: Optional[str]) -> Optional[str]:
        return validate_hh_mm(value) if value else value

    @field_validator("name")
    @classmethod
    def check_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not 1 <= len(value) <= 80:
            raise ValueError("Name must be 1 to 80 characters")
        return value
