from fastapi import Request
from starlette.responses import PlainTextResponse

from personal_growth_agent.common import logger


def base_exception_handler(request: Request, exc: Exception) -> PlainTextResponse:
    logger.exception(f"Unhandled error on {request.method} {request.url.path}", exc_info=exc)
    return PlainTextResponse("Internal Server Error", status_code=500)
