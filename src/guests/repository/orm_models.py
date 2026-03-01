from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config.table_names import TableNames
from src.guests.dtos import DietaryType, GuestStatus, GuestType, Language
from src.models.base import Base, TimeStamp


class Family(Base, TimeStamp):
    __tablename__ = TableNames.FAMILIES.value

    name: Mapped[str] = mapped_column(String(255), nullable=True)

    # Relationship to guests
    members: Mapped[list["Guest"]] = relationship("Guest", back_populates="family")

    def __repr__(self) -> str:
        return f"<Family {self.name or self.uuid}>"


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
        return f"<DietaryOption {self.requirement_type} for guest {self.guest_id}>"


class Guest(Base, TimeStamp):
    __tablename__ = TableNames.GUESTS.value

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TableNames.USERS.value}.uuid", ondelete="CASCADE"),
        nullable=True,  # Nullable for children who don't have a User
        index=True,
    )
    first_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)

    # Guest type (adult or child)
    guest_type: Mapped[str] = mapped_column(
        Enum(GuestType, name="guest_type_enum", values_callable=lambda x: [e.value for e in x]),
        default=GuestType.ADULT,
        nullable=False,
    )

    # Family relationship
    family_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TableNames.FAMILIES.value}.uuid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    family: Mapped["Family | None"] = relationship("Family", back_populates="members")

    # Plus one relationships
    # plus_one_of_id: Points to the guest who brought this guest as their plus-one
    # (if set, this guest IS a plus-one)
    plus_one_of_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TableNames.GUESTS.value}.uuid", ondelete="SET NULL"),
        nullable=True,
    )
    # bring_a_plus_one_id: Points to the plus-one guest that this guest is bringing
    bring_a_plus_one_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{TableNames.GUESTS.value}.uuid", ondelete="SET NULL"),
        nullable=True,
    )

    # Notes
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    # Allergies (free-text field for any allergies or dietary restrictions)
    allergies: Mapped[str] = mapped_column(Text, nullable=True)
    # Preferred language for communication (emails, RSVP page)
    preferred_language: Mapped[str] = mapped_column(
        Enum(Language, name="language_enum", values_callable=lambda x: [e.value for e in x]),
        default=Language.EN,
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<Guest {self.name} - {self.status.value}>"


class RSVPInfo(Base, TimeStamp):
    __tablename__ = TableNames.RSVP_INFO.value

    guest_id: Mapped[UUID] = mapped_column(
        ForeignKey(f"{TableNames.GUESTS.value}.uuid", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        Enum(GuestStatus, name="guest_status_enum_v2"),
        default=GuestStatus.PENDING,
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    rsvp_token: Mapped[str] = mapped_column(String(36), nullable=False, unique=True, index=True)
    rsvp_link: Mapped[str] = mapped_column(String(255), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    # Track when invitation email was sent (None if not sent)
    email_sent_on: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )

    def __repr__(self) -> str:
        return f"<RSVPInfo {self.rsvp_token}>"


class EmailLog(Base, TimeStamp):
    __tablename__ = "email_logs"
    
    # Core identification
    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    resend_email_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True, unique=True)
    
    # Email parameters
    to_address: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    from_address: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    
    # Email bodies (stored for debugging/audit)
    html_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    text_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Email type and context
    email_type: Mapped[str] = mapped_column(
        Enum("invitation", "confirmation", "reminder", "plus_one_invite", "forwarded", name="email_type_enum"),
        nullable=False,
        index=True
    )
    
    # Foreign keys for context
    guest_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{TableNames.GUESTS.value}.uuid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(f"{TableNames.USERS.value}.uuid", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Delivery tracking
    status: Mapped[str] = mapped_column(
        Enum("pending", "sent", "delivered", "bounced", "failed", "complained", name="email_status_enum"),
        default="pending",
        nullable=False,
        index=True,
    )
    
    # Additional metadata
    language: Mapped[str | None] = mapped_column(
        Enum(Language, name="language_enum_ref", values_callable=lambda x: [e.value for e in x]),
        nullable=True,
    )
    
    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Webhook event tracking
    last_webhook_event: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_webhook_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self) -> str:
        return f"<EmailLog {self.resend_email_id} to={self.to_address} type={self.email_type} status={self.status}>"
