from dataclasses import dataclass
from enum import Enum
from uuid import UUID


class DietaryType(str, Enum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    HALAL = "halal"
    KOSHER = "kosher"
    NUT_ALLERGY = "nut_allergy"
    OTHER = "other"


class GuestStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DECLINED = "declined"


@dataclass(frozen=True)
class RSVPInfoDTO:
    """DTO for RSVP page info returned by read model."""

    token: str
    name: str
    event_name: str
    event_date: str
    event_location: str
    status: GuestStatus
    is_plus_one: bool
    plus_one_name: str | None = None


@dataclass(frozen=True)
class GuestDTO:
    """DTO for guest data."""

    id: UUID
    name: str
    status: GuestStatus
    is_plus_one: bool
    plus_one_name: str | None
    email: str


@dataclass(frozen=True)
class RSVPResponseDTO:
    """DTO for RSVP response."""

    message: str
    attending: bool
    status: GuestStatus
