from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime
from src.config.table_names import TableNames
from src.models.base import BaseModel


class Event(BaseModel):
    __tablename__ = TableNames.EVENTS.value

    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    date = Column(DateTime, nullable=False)
    location = Column(String(500), nullable=True)
    timezone = Column(String(50), default="UTC")

    def __repr__(self) -> str:
        return f"<Event {self.name} on {self.date}>"
