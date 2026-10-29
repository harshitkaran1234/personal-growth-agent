from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from personal_growth_agent.common import config, logger

from .common.exception_handler import (
    base_exception_handler,
    custom_http_exception,
    custom_http_exception_handler,
)


def register_handlers(app: FastAPI) -> None:
    app.add_exception_handler(custom_http_exception, custom_http_exception_handler)
    app.add_exception_handler(Exception, base_exception_handler)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info(f"Starting {config.SERVICE_NAME} ({config.ENVIRONMENT})")
    yield
    logger.info(f"Stopping {config.SERVICE_NAME}")


def create_app() -> FastAPI:
    current_app = FastAPI(
        title="Personal Growth Agent",
        lifespan=lifespan,
    )
    current_app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ALLOW_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    from personal_growth_agent.routes import router

    current_app.include_router(router)
    register_handlers(current_app)
    return current_app


app = create_app()
