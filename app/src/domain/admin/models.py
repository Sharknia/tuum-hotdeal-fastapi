import enum

from sqlalchemy import Column, DateTime, Enum, Integer, Text

from app.src.core.database import Base
from app.src.core.time import utc_now


class WorkerStatus(enum.Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    RUNNING = "RUNNING"


class WorkerLog(Base):
    __tablename__ = "worker_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    status = Column(Enum(WorkerStatus), nullable=False)
    items_found = Column(Integer, default=0)
    emails_sent = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
