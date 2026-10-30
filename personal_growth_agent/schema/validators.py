import re

HH_MM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def validate_hh_mm(value: str) -> str:
    if not HH_MM.match(value):
        raise ValueError("Time must be in 24-hour HH:MM format")
    return value
