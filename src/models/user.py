from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from src.config.table_names import TableNames
from src.models.base import Base, TimeStamp


class User(Base, TimeStamp):
    __tablename__ = TableNames.USERS.value

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
