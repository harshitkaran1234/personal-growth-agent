from datetime import datetime

from .base import Base


class OtpRequest(Base):
    """One pending login code per email. Removed by a TTL index once expires_at passes."""

    __collection__ = "otp_request"

    email: str
    otp_hash: str
    expires_at: datetime
    retry_after: datetime
    match_fail_count: int = 0
