from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import EmailStr

if TYPE_CHECKING:
    from src.guests.repository.orm_models import Guest


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


class GuestType(str, Enum):
    ADULT = "adult"
    CHILD = "child"


class Language(str, Enum):
    EN = "en"
    ES = "es"
    NL = "nl"


@dataclass(frozen=True)
class PlusOneDTO:
    """DTO for plus one guest data used in RSVP submission."""

    email: EmailStr
    first_name: str
    last_name: str


@dataclass(frozen=True)
class FamilyMemberDTO:
    """DTO for family member info in RSVP response."""

    uuid: UUID
    first_name: str
    last_name: str
    guest_type: str = "adult"  # "adult" or "child"
    attending: bool | None = None
    dietary_requirements: list[dict] = field(default_factory=list)
    phone: str | None = None
    allergies: str | None = None

    @classmethod
    def from_guest(
        cls,
        guest: "Guest",
        rsvp_status: GuestStatus | None = None,
        dietary_requirements: list[dict] | None = None,
    ) -> "FamilyMemberDTO":
        """Create FamilyMemberDTO from Guest ORM model."""
        attending = None
        if rsvp_status == GuestStatus.CONFIRMED:
            attending = True
        elif rsvp_status == GuestStatus.DECLINED:
            attending = False

        return cls(
            uuid=guest.uuid,
            first_name=guest.first_name,
            last_name=guest.last_name,
            guest_type=getattr(guest, "guest_type", "adult"),
            attending=attending,
            dietary_requirements=dietary_requirements or [],
            phone=guest.phone,
            allergies=getattr(guest, "allergies", None),
        )


@dataclass(frozen=True)
class RSVPInfoDTO:
    """DTO for RSVP page info returned by read model."""

    guest_uuid: UUID
    token: str
    first_name: str
    last_name: str
    status: GuestStatus
    phone: str | None = None
    # plus_one_of_id presence indicates this guest is a plus-one
    plus_one_of_id: UUID | None = None
    # Family info
    family_id: UUID | None = None
    family_members: list[FamilyMemberDTO] = field(default_factory=list)
    # Plus-one guest details (from bring_a_plus_one_id join)
    plus_one_email: str | None = None
    plus_one_first_name: str | None = None
    plus_one_last_name: str | None = None
    # Prefill fields
    attending: bool | None = None
    dietary_requirements: list[dict] = field(default_factory=list)
    allergies: str | None = None


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
    family_id: UUID | None = None
    notes: str | None = None
