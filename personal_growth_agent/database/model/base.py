import math
from time import time
from typing import Any, ClassVar, Optional, Self

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.asynchronous.client_session import AsyncClientSession
from pymongo.asynchronous.collection import AsyncCollection
from pydantic import BaseModel, ConfigDict, Field

from ..db_client import db_client


class Base(BaseModel):
    __collection__: ClassVar[str]

    id: Optional[ObjectId] = Field(alias="_id", exclude=True, default=None)
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
    )

    @classmethod
    def collection(cls) -> AsyncCollection[dict[str, Any]]:
        return db_client.db[cls.__collection__]

    @classmethod
    async def find_by_id(
        cls, _id: str | ObjectId, session: Optional[AsyncClientSession] = None
    ) -> Self | None:
        result = await cls.collection().find_one(
            {"_id": ObjectId(_id) if isinstance(_id, str) else _id}, session=session
        )
        return cls.model_validate(result) if result else None

    @classmethod
    async def find_one_by_filter(
        cls, query: dict[str, Any], session: Optional[AsyncClientSession] = None
    ) -> Self | None:
        result = await cls.collection().find_one(query, session=session)
        return cls.model_validate(result) if result else None

    @classmethod
    async def find_many(
        cls,
        query: dict[str, Any],
        sort: Optional[list[tuple[str, int]]] = None,
        session: Optional[AsyncClientSession] = None,
    ) -> list[Self]:
        cursor = cls.collection().find(query, sort=sort, session=session)
        return [cls.model_validate(doc) async for doc in cursor]

    async def insert(self, session: Optional[AsyncClientSession] = None) -> Self:
        if not self.created_at:
            self.created_at = math.floor(time())
            self.updated_at = self.created_at
        self_dump = self.model_dump()
        self_dump["_id"] = self.id if self.id else ObjectId()
        self.id = (await self.collection().insert_one(self_dump, session=session)).inserted_id
        return self

    @classmethod
    async def find_one_and_update(
        cls,
        query: dict[str, Any],
        patch: dict[str, Any],
        upsert: bool = False,
        session: Optional[AsyncClientSession] = None,
    ) -> Self | None:
        patch.setdefault("$set", {}).update({"updated_at": math.floor(time())})
        result = await cls.collection().find_one_and_update(
            query, patch, upsert=upsert, return_document=ReturnDocument.AFTER, session=session
        )
        return cls.model_validate(result) if result else None

    @classmethod
    async def update_many(
        cls,
        query: dict[str, Any],
        patch: dict[str, Any],
        session: Optional[AsyncClientSession] = None,
    ) -> int:
        patch.setdefault("$set", {}).update({"updated_at": math.floor(time())})
        result = await cls.collection().update_many(query, patch, session=session)
        return result.modified_count

    @classmethod
    async def delete_many(
        cls, query: dict[str, Any], session: Optional[AsyncClientSession] = None
    ) -> int:
        result = await cls.collection().delete_many(query, session=session)
        return result.deleted_count

    async def update(
        self, patch: dict[str, Any], session: Optional[AsyncClientSession] = None
    ) -> Self | None:
        return await self.find_one_and_update({"_id": self.id}, patch, session=session)

    async def delete(self, session: Optional[AsyncClientSession] = None) -> None:
        await self.collection().delete_one({"_id": self.id}, session=session)
