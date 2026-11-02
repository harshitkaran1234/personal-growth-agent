import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

HH_MM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def validate_hh_mm(value: str) -> str:
    if not HH_MM.match(value):
        raise ValueError("Time must be in 24-hour HH:MM format")
    return value


def validate_timezone(value: str) -> str:
    try:
        ZoneInfo(value)
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError(f'"{value}" is not an IANA time zone like "Asia/Kolkata"')
    return value
