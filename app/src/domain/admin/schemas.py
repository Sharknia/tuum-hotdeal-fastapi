from pydantic import BaseModel
from app.src.domain.user.schemas import UserResponse

class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
