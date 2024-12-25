from sqlalchemy import (
    Column, 
    String, 
    Boolean, 
    DateTime, 
    Integer,
    Enum as SQLAlchemyEnum
)
from sqlalchemy.sql import func
import enum
from .base import BaseModel

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    USER = "user"

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"

class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    role = Column(SQLAlchemyEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SQLAlchemyEnum(UserStatus), default=UserStatus.PENDING, nullable=False)
    
    # Campi di sicurezza
    is_active = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime(timezone=True), nullable=True)
    
    # Campi di audit
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    activation_token = Column(String(255), nullable=True)
    reset_password_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>" 