import time
from collections.abc import Awaitable, Callable
from datetime import date
from typing import Any, Optional, Protocol, TypeVar, runtime_checkable

from bson import ObjectId
from pydantic import BaseModel
from pymongo.asynchronous.client_session import AsyncClientSession

from personal_growth_agent.common.exceptions import (
    InvalidRequestException,
    ResourceNotFoundException,
)
from personal_growth_agent.database import db_client
from personal_growth_agent.database import model as db
from personal_growth_agent.database.model import (
    Commitment,
    Goal,
    GoalStatus,
    Milestone,
    Profile,
    User,
)
from personal_growth_agent.schema import (
    AvoidCommitment,
    CurrentGoal,
    CurrentPlan,
    PendingPlan,
    PlanDraft,
    PracticeCommitment,
    ProfileDraft,
    ProposedCommitment,
    ProposedGoal,
    ProposedMilestone,
)

T = TypeVar("T")
GOAL_FIELDS = {"title", "why", "type", "priority", "commitment", "milestones", "target_date"}


@runtime_checkable
class PlanStore(Protocol):
    async def current(self, user_id: str) -> CurrentPlan: ...

    async def pending(self, user_id: str) -> Optional[PendingPlan]: ...

    async def present(self, user_id: str, plan: PlanDraft) -> PendingPlan: ...

    async def confirm(self, user_id: str, version: int) -> int: ...


def to_db_commitment(commitment: ProposedCommitment) -> Commitment:
    if isinstance(commitment, PracticeCommitment):
        return db.PracticeCommitment(**commitment.model_dump())
    return db.AvoidCommitment(**commitment.model_dump())


def to_plan_commitment(commitment: Commitment) -> ProposedCommitment:
    if isinstance(commitment, db.PracticeCommitment):
        return PracticeCommitment(**commitment.model_dump())
    return AvoidCommitment(**commitment.model_dump())


def to_goal(
    user_id: ObjectId, goal: ProposedGoal, source_goal_id: Optional[ObjectId] = None
) -> Goal:
    return Goal(
        user_id=user_id,
        title=goal.title,
        why=goal.why,
        type=goal.type,
        status=GoalStatus.DRAFT,
        priority=goal.priority,
        commitment=to_db_commitment(goal.commitment),
        milestones=[
            Milestone(title=m.title, due_date=m.due_date.isoformat()) for m in goal.milestones
        ],
        target_date=goal.target_date.isoformat() if goal.target_date else None,
        source_goal_id=source_goal_id,
    )


def to_proposed(goal: Goal, ref: Optional[str] = None) -> ProposedGoal:
    return ProposedGoal(
        ref=ref,
        title=goal.title,
        why=goal.why or "",
        type=goal.type,
        commitment=to_plan_commitment(goal.commitment),
        target_date=date.fromisoformat(goal.target_date) if goal.target_date else None,
        milestones=[
            ProposedMilestone(title=m.title, due_date=date.fromisoformat(m.due_date))
            for m in goal.milestones
            if m.due_date
        ],
        priority=goal.priority or 1,
    )


def to_profile_draft(profile: Profile) -> ProfileDraft:
    return ProfileDraft(**profile.model_dump())


def active_profile(user: User) -> Optional[Profile]:
    if not user.is_onboarded or not user.name:
        return None
    return Profile(
        name=user.name,
        reminder_time=user.reminder_time,
        review_day=user.review_day,
        timezone=user.timezone,
    )


def goal_fields(goal: Goal) -> dict[str, Any]:
    return goal.model_dump(include=GOAL_FIELDS, exclude={"milestones": {"__all__": {"id"}}})


def is_goal_changed(draft: Goal, source: Goal) -> bool:
    return goal_fields(draft) != goal_fields(source)


class MongoPlanStore(BaseModel):
    async def current(self, user_id: str) -> CurrentPlan:
        oid = ObjectId(user_id)
        user = await self._user(oid)
        refs = await self.active_goals(oid)
        goals = [CurrentGoal(ref=ref, goal=to_proposed(goal, ref)) for ref, goal in refs.items()]
        profile = active_profile(user)
        return CurrentPlan(goals=goals, profile=to_profile_draft(profile) if profile else None)

    async def pending(self, user_id: str) -> Optional[PendingPlan]:
        oid = ObjectId(user_id)
        user = await self._user(oid)
        drafts = await self.draft_goals(oid)
        if not drafts or user.pending_profile is None:
            return None
        ref_of = {goal.id: ref for ref, goal in (await self.active_goals(oid)).items()}
        goals = [to_proposed(d, ref_of.get(d.source_goal_id)) for d in drafts]
        plan = PlanDraft(goals=goals, profile=to_profile_draft(user.pending_profile))
        return PendingPlan(version=user.plan_version, plan=plan)

    async def present(self, user_id: str, plan: PlanDraft) -> PendingPlan:
        oid = ObjectId(user_id)

        async def write(session: AsyncClientSession) -> PendingPlan:
            user = await self._user(oid, session)
            refs = await self.active_goals(oid, session)
            unknown = [g.ref for g in plan.goals if g.ref and g.ref not in refs]
            if unknown:
                known = ", ".join(refs) or "none"
                raise InvalidRequestException(
                    f"{', '.join(unknown)} is not a current goal. Current goals: {known}"
                )
            await Goal.delete_many({"user_id": oid, "status": GoalStatus.DRAFT}, session=session)
            for goal in plan.goals:
                source = refs[goal.ref].id if goal.ref else None
                await to_goal(oid, goal, source).insert(session=session)
            updated = await User.find_one_and_update(
                {"_id": user.id},
                {
                    "$set": {"pending_profile": plan.profile.model_dump()},
                    "$inc": {"plan_version": 1},
                },
                session=session,
            )
            assert updated is not None
            return PendingPlan(version=updated.plan_version, plan=plan)

        return await self._transaction(write)

    async def confirm(self, user_id: str, version: int) -> int:
        oid = ObjectId(user_id)

        async def write(session: AsyncClientSession) -> int:
            user = await self._user(oid, session)
            drafts = await Goal.find_many(
                {"user_id": oid, "status": GoalStatus.DRAFT}, session=session
            )
            if not drafts or user.pending_profile is None:
                raise ResourceNotFoundException("There is no plan waiting for confirmation")
            if version != user.plan_version:
                raise InvalidRequestException(
                    f"Plan version {version} is not the latest; the latest is {user.plan_version}"
                )
            kept = {d.source_goal_id for d in drafts if d.source_goal_id}
            now = int(time.time())
            await Goal.update_many(
                {"user_id": oid, "status": GoalStatus.ACTIVE, "_id": {"$nin": list(kept)}},
                {"$set": {"status": GoalStatus.ARCHIVED, "archived_at": now}},
                session=session,
            )
            for draft in drafts:
                if draft.source_goal_id:
                    fields: dict[str, Any] = draft.model_dump(include=GOAL_FIELDS)
                    await Goal.find_one_and_update(
                        {"_id": draft.source_goal_id, "user_id": oid},
                        {"$set": fields},
                        session=session,
                    )
                    await draft.delete(session=session)
                else:
                    await draft.update({"$set": {"status": GoalStatus.ACTIVE}}, session=session)
            await User.find_one_and_update(
                {"_id": oid},
                {
                    "$set": {**user.pending_profile.model_dump(), "is_onboarded": True},
                    "$unset": {"pending_profile": ""},
                },
                session=session,
            )
            return len(drafts)

        return await self._transaction(write)

    @staticmethod
    async def _user(oid: ObjectId, session: Optional[AsyncClientSession] = None) -> User:
        user = await User.find_by_id(oid, session=session)
        if user is None:
            raise ResourceNotFoundException("User not found")
        return user

    @staticmethod
    async def active_goals(
        oid: ObjectId, session: Optional[AsyncClientSession] = None
    ) -> dict[str, Goal]:
        goals = await Goal.find_many(
            {"user_id": oid, "status": GoalStatus.ACTIVE},
            sort=[("priority", 1), ("created_at", 1), ("_id", 1)],
            session=session,
        )
        return {f"g{i}": goal for i, goal in enumerate(goals, start=1)}

    @staticmethod
    async def draft_goals(oid: ObjectId) -> list[Goal]:
        return await Goal.find_many(
            {"user_id": oid, "status": GoalStatus.DRAFT}, sort=[("priority", 1), ("_id", 1)]
        )

    @staticmethod
    async def _transaction(callback: Callable[[AsyncClientSession], Awaitable[T]]) -> T:
        assert db_client.client is not None
        async with db_client.client.start_session() as session:
            return await session.with_transaction(callback)
