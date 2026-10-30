import os
from pathlib import Path
from typing import Optional

import dotenv
from pydantic_settings import BaseSettings

from .logger import logger

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Config(BaseSettings):
    def __init__(self) -> None:
        if "ENVIRONMENT" not in os.environ:
            env_name = ".env"
        elif "staging" in os.environ["ENVIRONMENT"]:
            env_name = ".staging.env"
        elif "dev" in os.environ["ENVIRONMENT"]:
            env_name = ".dev.env"
        else:
            env_name = ".env"
        env_path = PROJECT_ROOT / env_name
        logger.info(f"Loading env from {env_path}")
        if env_path.exists():
            dotenv.load_dotenv(env_path)
        else:
            logger.warning(f"Environment file not found at {env_path}")
        super().__init__()

    ENVIRONMENT: str = "local"
    SERVICE_NAME: str = "personal-growth-agent"
    CORS_ALLOW_ORIGINS: list[str] = ["http://localhost:3000"]

    MONGO_CONNECTION_URI: str
    MONGO_DB_NAME: str = "personal_growth_agent"
    MONGO_CONNECTION_POOL: int = 100

    JWT_SECRET: str
    JWT_EXPIRY_TIME: int = 7 * 24 * 60 * 60

    DEFAULT_REMINDER_TIME: str = "21:00"

    OTP_EXPIRE_TIME: int = 10 * 60
    OTP_RETRY_COOLDOWN: int = 30
    OTP_FAILURE_LIMIT: int = 5
    HARDCODED_OTP: Optional[str] = None


config = Config()
