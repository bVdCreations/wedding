from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.config.table_names import TableNames
from src.guests.dtos import DietaryType, GuestStatus
from src.models.base import Base, TimeStamp


class DietaryOption(Base, TimeStamp):
    __tablename__ = TableNames.DIETARY_OPTIONS.value

    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TableNames.GUESTS.value}.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    requirement_type: Mapped[str] = mapped_column(
        Enum(DietaryType, name="dietary_type_enum"), nullable=False
    )
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DietaryOption {self.requirement_type.value} for guest {self.guest_id}>"


class Guest(Base, TimeStamp):
    __tablename__ = TableNames.GUESTS.value

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TableNames.USERS.value}.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)

    # RSVP status
    status: Mapped[str] = mapped_column(
        Enum(GuestStatus, name="guest_status_enum"),
        default=GuestStatus.PENDING,
        nullable=False,
    )

    # Plus one
    is_plus_one: Mapped[bool] = mapped_column(Boolean, default=False)
    plus_one_of_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TableNames.USERS.value}.uuid", ondelete="SET NULL"),
        nullable=True,
    )
    plus_one_name: Mapped[str] = mapped_column(String(255), nullable=True)

    # RSVP token for unique invitation links
    rsvp_token: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)

    # Notes
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Guest {self.name} - {self.status.value}>"
