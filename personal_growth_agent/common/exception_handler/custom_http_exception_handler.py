from fastapi import Request
from fastapi.responses import JSONResponse

from personal_growth_agent.common.exceptions import CustomException


def custom_http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, CustomException)
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


exception = CustomException
