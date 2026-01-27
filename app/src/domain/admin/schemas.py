from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.src.domain.user.schemas import UserResponse
from app.src.domain.hotdeal.schemas import KeywordResponse
from app.src.domain.admin.models import WorkerStatus

class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int


class WorkerLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_at: datetime
    status: WorkerStatus
    items_found: int
    message: str | None = None
    details: str | None = None


class KeywordListResponse(BaseModel):
    items: list[KeywordResponse]


class WorkerLogListResponse(BaseModel):
    items: list[WorkerLogResponse]
