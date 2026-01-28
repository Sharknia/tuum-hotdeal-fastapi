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
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    keywords = relationship("Keyword", secondary=user_keywords, back_populates="users")
    mail_logs = relationship("MailLog", back_populates="user")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="user", cascade="all, delete-orphan"
    )


class RefreshToken(Base):
    """다중 세션 지원을 위한 리프레시 토큰 모델"""

    __tablename__ = "refresh_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # SHA-256 해시된 토큰 (64 chars)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    user_agent = Column(String(512), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="refresh_tokens")
