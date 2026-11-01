from pydantic import BaseModel, ConfigDict

from personal_growth_agent.core.goals import PlanStore


class GoalPlannerContext(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: str
    store: PlanStore
