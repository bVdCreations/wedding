from enum import Enum as PyEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.config.table_names import TableNames
from src.models.base import Base, TimeStamp


class DietaryType(str, PyEnum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    HALAL = "halal"
    KOSHER = "kosher"
    NUT_ALLERGY = "nut_allergy"
    OTHER = "other"


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
