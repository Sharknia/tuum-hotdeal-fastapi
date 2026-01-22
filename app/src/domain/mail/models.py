from datetime import UTC, datetime

from sqlalchemy import UUID, Column, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.src.core.database import Base


class MailLog(Base):
    __tablename__ = "mail_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    keyword_id = Column(Integer, ForeignKey("hotdeal_keywords.id"), nullable=False)
    sent_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    user = relationship("User", back_populates="mail_logs")
    keyword = relationship("Keyword", back_populates="mail_logs")
