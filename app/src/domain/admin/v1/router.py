from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies.auth import authenticate_admin_user
from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.user.repositories import get_all_users, activate_user
from app.src.domain.user.schemas import AuthenticatedUser, UserResponse
from app.src.domain.admin.schemas import UserListResponse
from app.worker_main import job

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get("/users", response_model=UserListResponse, summary="사용자 목록 조회")
async def get_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[AuthenticatedUser, Depends(authenticate_admin_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
):
    users = await get_all_users(db, skip=skip, limit=limit)
    return {"items": users, "total": len(users)}


@router.patch("/users/{user_id}/approve", response_model=UserResponse, summary="사용자 승인")
async def approve_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[AuthenticatedUser, Depends(authenticate_admin_user)],
):
    user = await activate_user(db, user_id)
    if not user:
        raise AuthErrors.USER_NOT_FOUND
    return user


@router.post(
    "/hotdeals/trigger-search",
    status_code=status.HTTP_202_ACCEPTED,
    summary="수동으로 핫딜 검색을 실행합니다. (관리자 권한 필요)",
)
async def trigger_hotdeal_search(
    background_tasks: BackgroundTasks,
    # 아래 의존성 주입으로 관리자 권한을 가진 사용자만 이 엔드포인트에 접근할 수 있습니다.
    _: AuthenticatedUser = Depends(authenticate_admin_user),
):
    """
    백그라운드에서 핫딜 크롤링 및 분석 작업을 실행합니다.
    작업 실행 요청만 받고 즉시 응답을 반환하며, 실제 작업은 비동기적으로 처리됩니다.
    """
    background_tasks.add_task(job)
    return {"message": "핫딜 검색 작업이 백그라운드에서 시작되었습니다."}
