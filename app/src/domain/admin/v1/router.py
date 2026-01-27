from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies.auth import authenticate_admin_user
from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.admin.repositories import get_all_worker_logs
from app.src.domain.admin.schemas import (
    KeywordListResponse,
    UserDetailResponse,
    UserListResponse,
    WorkerLogListResponse,
)
from app.src.domain.hotdeal.repositories import delete_keyword, get_all_keywords
from app.src.domain.user.repositories import (
    activate_user,
    deactivate_user,
    get_all_users,
    get_user_with_keywords,
)
from app.src.domain.user.schemas import AuthenticatedUser, UserResponse
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


@router.patch(
    "/users/{user_id}/unapprove", response_model=UserResponse, summary="사용자 승인 해제"
)
async def unapprove_user(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[AuthenticatedUser, Depends(authenticate_admin_user)],
):
    user = await deactivate_user(db, user_id)
    if not user:
        raise AuthErrors.USER_NOT_FOUND
    return user


@router.get("/users/{user_id}", response_model=UserDetailResponse, summary="사용자 상세 조회")
async def get_user_detail(
    user_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[AuthenticatedUser, Depends(authenticate_admin_user)],
):
    user = await get_user_with_keywords(db, user_id)
    if not user:
        raise AuthErrors.USER_NOT_FOUND
    return user


@router.get("/keywords", response_model=KeywordListResponse, summary="전체 키워드 조회")
async def get_keywords(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[AuthenticatedUser, Depends(authenticate_admin_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
):
    keywords = await get_all_keywords(db, skip=skip, limit=limit)
    return {"items": keywords}


@router.delete(
    "/keywords/{keyword_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="키워드 삭제",
)
async def remove_keyword(
    keyword_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[AuthenticatedUser, Depends(authenticate_admin_user)],
):
    await delete_keyword(db, keyword_id)


@router.get("/logs", response_model=WorkerLogListResponse, summary="워커 로그 조회")
async def get_logs(
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[AuthenticatedUser, Depends(authenticate_admin_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
):
    logs = await get_all_worker_logs(db, skip=skip, limit=limit)
    return {"items": logs}


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
