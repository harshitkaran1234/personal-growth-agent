from typing import Any, Optional

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from personal_growth_agent.common import config, logger


class DatabaseNotInitialized(Exception):
    pass


class MongoDBClient:
    client: Optional[AsyncMongoClient[dict[str, Any]]] = None
    _db: Optional[AsyncDatabase[dict[str, Any]]] = None

    def init(self) -> None:
        logger.info("Initializing mongodb client")
        self.client = AsyncMongoClient(
            config.MONGO_CONNECTION_URI, maxPoolSize=config.MONGO_CONNECTION_POOL, tz_aware=True
        )
        self._db = self.client.get_database(config.MONGO_DB_NAME)

    async def close(self) -> None:
        logger.info("Closing mongodb client")
        if self.client is not None:
            await self.client.close()
        self.client = None
        self._db = None

    @property
    def db(self) -> AsyncDatabase[dict[str, Any]]:
        if self._db is None:
            raise DatabaseNotInitialized("Database client is not initialized.")
        return self._db


db_client = MongoDBClient()
