from datetime import datetime, timedelta, timezone

from personal_growth_agent.common import config, logger
from personal_growth_agent.core.auth import generate_otp, hash_otp, send_otp_email
from personal_growth_agent.database.model import OtpRequest

from ..schema import EmailOTPRequest, EmailOTPResponse


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def send_email_otp(request: EmailOTPRequest) -> EmailOTPResponse:
    email = normalize_email(request.email)
    now = datetime.now(timezone.utc)

    existing = await OtpRequest.find_one_by_filter({"email": email})
    if existing and existing.expires_at > now and existing.retry_after > now:
        logger.info(f"[send_email_otp] Cooldown active for {email}, not resending")
        return EmailOTPResponse(
            email=email,
            expires_at=int(existing.expires_at.timestamp()),
            retry_after=int(existing.retry_after.timestamp()),
        )

    otp = generate_otp()
    expires_at = now + timedelta(seconds=config.OTP_EXPIRE_TIME)
    retry_after = now + timedelta(seconds=config.OTP_RETRY_COOLDOWN)
    await OtpRequest.find_one_and_update(
        {"email": email},
        {
            "$set": {
                "otp_hash": hash_otp(email, otp),
                "expires_at": expires_at,
                "retry_after": retry_after,
                "match_fail_count": 0,
            },
            "$setOnInsert": {"email": email, "created_at": int(now.timestamp())},
        },
        upsert=True,
    )
    await send_otp_email(email, otp)
    logger.info(f"[send_email_otp] OTP issued for {email}")

    return EmailOTPResponse(
        email=email,
        expires_at=int(expires_at.timestamp()),
        retry_after=int(retry_after.timestamp()),
    )
