from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum
from app.src.core.database import Base
import enum

class WorkerStatus(enum.Enum):
    SUCCESS = "SUCCESS"
    FAIL = "FAIL"
    RUNNING = "RUNNING"

class WorkerLog(Base):
    __tablename__ = "worker_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_at = Column(DateTime, default=datetime.now, nullable=False)
    status = Column(Enum(WorkerStatus), nullable=False)
    items_found = Column(Integer, default=0)
    message = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
