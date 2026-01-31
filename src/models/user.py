from sqlalchemy import Column, String, Boolean
from src.config.table_names import TableNames
from src.models.base import BaseModel


class User(BaseModel):
    __tablename__ = TableNames.USERS.value

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
