from datetime import datetime
from pathlib import Path
from typing import Protocol, runtime_checkable

from pydantic import BaseModel

from personal_growth_agent.common.config import PROJECT_ROOT
from personal_growth_agent.common.exceptions import (
    InvalidRequestException,
    ResourceNotFoundException,
)
from personal_growth_agent.schema import ConfirmedPlan, PendingPlan, PlanDraft, PlanRecord


@runtime_checkable
class PlanStore(Protocol):
    async def get(self, user_id: str) -> PlanRecord: ...

    async def present(self, user_id: str, plan: PlanDraft) -> PendingPlan: ...

    async def confirm(self, user_id: str, version: int) -> ConfirmedPlan: ...


class JsonPlanStore(BaseModel):
    root: Path = PROJECT_ROOT / "data" / "plans"

    async def get(self, user_id: str) -> PlanRecord:
        path = self._path(user_id)
        if not path.exists():
            return PlanRecord(user_id=user_id)
        return PlanRecord.model_validate_json(path.read_text())

    async def present(self, user_id: str, plan: PlanDraft) -> PendingPlan:
        record = await self.get(user_id)
        latest = max(
            (p.version for p in (record.pending, record.confirmed) if p is not None), default=0
        )
        record.pending = PendingPlan(version=latest + 1, presented_at=datetime.now(), plan=plan)
        self._write(record)
        return record.pending

    async def confirm(self, user_id: str, version: int) -> ConfirmedPlan:
        record = await self.get(user_id)
        if record.pending is None:
            raise ResourceNotFoundException("There is no plan waiting for confirmation")
        if record.pending.version != version:
            raise InvalidRequestException(
                f"Plan version {version} is out of date; the latest is {record.pending.version}"
            )
        record.confirmed = ConfirmedPlan(
            version=version, confirmed_at=datetime.now(), plan=record.pending.plan
        )
        record.pending = None
        self._write(record)
        return record.confirmed

    def _path(self, user_id: str) -> Path:
        return self.root / f"{user_id}.json"

    def _write(self, record: PlanRecord) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        self._path(record.user_id).write_text(record.model_dump_json(indent=2))
