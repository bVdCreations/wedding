from datetime import datetime
from uuid import UUID, uuid4

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, declarative_base, mapped_column
from sqlalchemy_utils import UUIDType

BaseModel = declarative_base()


class Base(BaseModel):
    __abstract__ = True

    type_annotation_map = {
        UUID: UUIDType,
    }

    uuid: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)


class TimeStamp(BaseModel):
    __abstract__ = True

    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.current_timestamp(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        server_default=sa.func.current_timestamp(),
        onupdate=sa.func.current_timestamp(),
        nullable=False,
    )
