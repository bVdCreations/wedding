from dataclasses import dataclass, field
from enum import Enum
from uuid import UUID

from pydantic import EmailStr


class GuestAlreadyExistsError(Exception):
    """Raised when trying to create a guest for a user who already has one."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"User with email '{email}' already has a guest account")


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
class PlusOneDTO:
    """DTO for plus one guest data used in RSVP submission."""

    email: EmailStr
    first_name: str
    last_name: str


@dataclass(frozen=True)
class RSVPInfoDTO:
    """DTO for RSVP page info returned by read model."""

    token: str
    name: str
    status: GuestStatus
    # plus_one_of_id presence indicates this guest is a plus-one
    plus_one_of_id: UUID | None = None
    # Plus-one guest details (from bring_a_plus_one_id join)
    plus_one_email: str | None = None
    plus_one_first_name: str | None = None
    plus_one_last_name: str | None = None
    # Prefill fields
    attending: bool | None = None
    dietary_requirements: list[dict] = field(default_factory=list)


@dataclass(frozen=True)
class RSVPResponseDTO:
    """DTO for RSVP response."""

    message: str
    attending: bool
    status: GuestStatus


@dataclass(frozen=True)
class RSVPDTO:
    """DTO for RSVP response."""

    status: GuestStatus
    token: str
    link: str


@dataclass(frozen=True)
class GuestDTO:
    """DTO for guest data."""

    id: UUID
    email: str
    rsvp: RSVPDTO
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    # plus_one_of_id presence indicates this guest is a plus-one
    plus_one_of_id: UUID | None = None
    bring_a_plus_one_id: UUID | None = None
    notes: str | None = None
