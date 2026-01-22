from uuid import uuid4

from sqlalchemy import (
    UUID,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.src.core.database import Base

from .enums import AuthLevel

user_keywords = Table(
    "user_keywords",
    Base.metadata,
    Column("user_id", UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True),
    Column("keyword_id", Integer, ForeignKey("hotdeal_keywords.id"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    nickname = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    auth_level = Column(
        Integer, nullable=False, server_default=text(str(AuthLevel.USER.value))
    )
    is_active = Column(Boolean, nullable=False, server_default=text("false"))
    refresh_token = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    keywords = relationship("Keyword", secondary=user_keywords, back_populates="users")
    mail_logs = relationship("MailLog", back_populates="user")
