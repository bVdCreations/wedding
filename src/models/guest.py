from enum import Enum as PyEnum
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum, Text
from src.config.table_names import TableNames
from src.models.base import BaseModel


class GuestStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DECLINED = "declined"


class Guest(BaseModel):
    __tablename__ = TableNames.GUESTS.value

    event_id = Column(
        String(36),
        ForeignKey(f"{TableNames.EVENTS.value}.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)

    # RSVP status
    status = Column(
        Enum(GuestStatus, name="guest_status_enum"),
        default=GuestStatus.PENDING,
        nullable=False,
    )

    # Plus one
    is_plus_one = Column(Boolean, default=False)
    plus_one_of_id = Column(
        String(36),
        ForeignKey(f"{TableNames.GUESTS.value}.id", ondelete="SET NULL"),
        nullable=True,
    )
    plus_one_name = Column(String(255), nullable=True)

    # RSVP token for unique invitation links
    rsvp_token = Column(String(36), unique=True, nullable=False, index=True)

    # Notes
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<Guest {self.name} - {self.status.value}>"
