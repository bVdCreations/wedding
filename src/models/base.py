import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime
from src.config.database import Base


class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class UUIDMixin:
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))


class BaseModel(UUIDMixin, TimestampMixin, Base):
    __abstract__ = True
