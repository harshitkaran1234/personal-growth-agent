from fastapi import APIRouter

from .controller import send_email_otp, validate_email_otp
from .schema import EmailOTPRequest, EmailOTPResponse, ValidateOTPRequest, ValidateOTPResponse

router = APIRouter(prefix="/email", tags=["Auth"])


@router.post("/otp")
async def post_email_otp(request: EmailOTPRequest) -> EmailOTPResponse:
    return await send_email_otp(request)


@router.post("/otp/validate")
async def validate_otp(request: ValidateOTPRequest) -> ValidateOTPResponse:
    return await validate_email_otp(request)
