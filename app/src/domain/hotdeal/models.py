from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.src.core.database import Base
from app.src.domain.hotdeal.enums import SiteName


class Keyword(Base):
    __tablename__ = "hotdeal_keywords"
    __table_args__ = (UniqueConstraint("title", name="uq_keywords_title"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    wdate = Column(DateTime, default=lambda: datetime.now(), nullable=False)

    users = relationship("User", secondary="user_keywords", back_populates="keywords")
    mail_logs = relationship("MailLog", back_populates="keyword")
    sites = relationship(
        "KeywordSite", back_populates="keyword", cascade="all, delete-orphan"
    )


class KeywordSite(Base):
    __tablename__ = "hotdeal_keyword_sites"

    keyword_id = Column(
        Integer, ForeignKey("hotdeal_keywords.id"), primary_key=True, nullable=False
    )
    site_name = Column(Enum(SiteName), primary_key=True, nullable=False)
    external_id = Column(String, nullable=False)
    link = Column(String, nullable=True)
    price = Column(String, nullable=True)
    meta_data = Column(Text, nullable=True)
    wdate = Column(DateTime, default=lambda: datetime.now(), nullable=False)

    keyword = relationship("Keyword", back_populates="sites")
