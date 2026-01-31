from enum import Enum as PyEnum
from sqlalchemy import Column, String, ForeignKey, Enum, Text
from src.config.table_names import TableNames
from src.models.base import BaseModel


class DietaryType(str, PyEnum):
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"
    GLUTEN_FREE = "gluten_free"
    DAIRY_FREE = "dairy_free"
    HALAL = "halal"
    KOSHER = "kosher"
    NUT_ALLERGY = "nut_allergy"
    OTHER = "other"


class DietaryOption(BaseModel):
    __tablename__ = TableNames.DIETARY_OPTIONS.value

    guest_id = Column(
        String(36),
        ForeignKey(f"{TableNames.GUESTS.value}.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    requirement_type = Column(
        Enum(DietaryType, name="dietary_type_enum"),
        nullable=False,
    )
    notes = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<DietaryOption {self.requirement_type.value} for guest {self.guest_id}>"
