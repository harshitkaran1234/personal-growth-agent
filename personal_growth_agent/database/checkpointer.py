from langgraph.checkpoint.mongodb import MongoDBSaver
from pymongo import MongoClient

from personal_growth_agent.common import config


def build_checkpointer() -> MongoDBSaver:
    return MongoDBSaver(
        MongoClient(config.MONGO_CONNECTION_URI),
        db_name=config.MONGO_DB_NAME,
        checkpoint_collection_name="agent_checkpoints",
        writes_collection_name="agent_checkpoint_writes",
    )
