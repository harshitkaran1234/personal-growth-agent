from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

# Calendar day as "YYYY-MM-DD". Stored as a string so "which day" never shifts with time zones.
DateStr = Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]


class Embedded(BaseModel):
    """Base for sub-documents stored inside a collection document."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
