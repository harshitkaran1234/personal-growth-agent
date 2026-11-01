from pydantic import BaseModel


class GoalLoad(BaseModel):
    title: str
    minutes: int


class WeeklyLoad(BaseModel):
    goals: list[GoalLoad]
    total_minutes: int
