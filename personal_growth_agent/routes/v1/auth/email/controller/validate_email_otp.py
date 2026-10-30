import time
from datetime import datetime, timezone

from personal_growth_agent.common import config, logger
from personal_growth_agent.common.exceptions import InvalidRequestException
from personal_growth_agent.core.auth import generate_jwt_token, otp_matches
from personal_growth_agent.database.model import OtpRequest, User

from ..schema import ValidateOTPRequest, ValidateOTPResponse
from .send_email_otp import normalize_email

INVALID_OTP = "OTP is either expired or invalid"


async def validate_email_otp(request: ValidateOTPRequest) -> ValidateOTPResponse:
    email = normalize_email(request.email)

    otp_request = await OtpRequest.find_one_by_filter({"email": email})
    if not otp_request:
        raise InvalidRequestException(INVALID_OTP)
    if otp_request.expires_at < datetime.now(timezone.utc):
        await otp_request.delete()
        raise InvalidRequestException(INVALID_OTP)
    if not otp_matches(email, request.otp.strip(), otp_request.otp_hash):
        # Drop the code after too many wrong guesses to stop brute forcing.
        if otp_request.match_fail_count + 1 >= config.OTP_FAILURE_LIMIT:
            await otp_request.delete()
        else:
            await otp_request.update({"$inc": {"match_fail_count": 1}})
        raise InvalidRequestException(INVALID_OTP)
    await otp_request.delete()

    now = int(time.time())
    user = await User.find_one_by_filter({"email": email})
    is_new_user = user is None
    if user is None:
        new_user = User(email=email, created_at=now, last_login_at=now)
        # Upsert so two logins racing for a new email still end with one account.
        user = await User.find_one_and_update(
            {"email": email},
            {"$setOnInsert": new_user.model_dump(exclude={"updated_at"})},
            upsert=True,
        )
        logger.info(f"[validate_email_otp] Created user for {email}")
    else:
        user = await user.update({"$set": {"last_login_at": now}})
    assert user is not None

    return ValidateOTPResponse(access_token=generate_jwt_token(user), is_new_user=is_new_user)
