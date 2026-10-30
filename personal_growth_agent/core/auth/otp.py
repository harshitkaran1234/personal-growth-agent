import hashlib
import hmac
import secrets

from personal_growth_agent.common import config, logger


def generate_otp() -> str:
    if config.HARDCODED_OTP:
        return config.HARDCODED_OTP
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_otp(email: str, otp: str) -> str:
    return hashlib.sha256(f"{config.JWT_SECRET}:{email}:{otp}".encode()).hexdigest()


def otp_matches(email: str, otp: str, otp_hash: str) -> bool:
    return hmac.compare_digest(hash_otp(email, otp), otp_hash)


async def send_otp_email(email: str, otp: str) -> None:
    """Deliver the login code. Placeholder until AWS SES is integrated."""
    if config.HARDCODED_OTP:
        logger.info(f"[send_otp_email] Hardcoded OTP in use, no email sent to {email}")
        return
    raise NotImplementedError("Email delivery is not configured. Set HARDCODED_OTP for now.")
