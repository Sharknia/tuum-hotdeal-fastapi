from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Cookie, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.dependencies.auth import authenticate_refresh_token, registered_user
from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.core.logger import logger
from app.src.domain.user.repositories import get_all_admins
from app.src.domain.user.schemas import (
    AuthenticatedUser,
    LoginResponse,
    LogoutResponse,
    UserCreateRequest,
    UserLoginRequest,
    UserResponse,
)
from app.src.domain.user.services import (
    create_new_user,
    get_user_info,
    login_user,
    logout_user,
    refresh_access_token,
    send_new_user_notifications,
)
from app.src.utils.swsagger_helper import create_responses

router = APIRouter(prefix="/v1", tags=["user"])


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="새로운 사용자 생성 (회원가입)",
    responses=create_responses(
        AuthErrors.EMAIL_ALREADY_REGISTERED,
    ),
)
async def signup(
    request: UserCreateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    background_tasks: BackgroundTasks,
) -> UserResponse:
    """
    새로운 사용자를 등록합니다.

    - **email**: 사용자 이메일 (로그인 시 사용)
    - **password**: 사용자 비밀번호
    - **nickname**: 사용자 닉네임
    """
    new_user: UserResponse = await create_new_user(
        db=db,
        email=request.email,
        nickname=request.nickname,
        password=request.password,
    )

    admins = await get_all_admins(db)
    if admins:
        background_tasks.add_task(send_new_user_notifications, admins, new_user)

    return new_user


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="사용자 로그인",
    responses=create_responses(
        AuthErrors.USER_NOT_FOUND,
        AuthErrors.INVALID_PASSWORD,
        AuthErrors.USER_NOT_ACTIVE,
    ),
)
async def login(
    request: Request,
    body: UserLoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LoginResponse:
    """
    사용자 로그인

    - **email**: 사용자 이메일 (로그인 시 사용)
    - **password**: 사용자 비밀번호
    """
    user: LoginResponse = await login_user(
        db=db,
        response=response,
        email=body.email,
        password=body.password,
        request=request,
    )
    return user


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="사용자 로그아웃",
    responses=create_responses(
        AuthErrors.INVALID_TOKEN,
        AuthErrors.INVALID_TOKEN_PAYLOAD,
        AuthErrors.USER_NOT_ACTIVE,
        AuthErrors.USER_NOT_FOUND,
    ),
)
async def logout(
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
    current_user: Annotated[AuthenticatedUser, Depends(registered_user)],
    refresh_token: str | None = Cookie(None),
) -> LogoutResponse:
    """
    사용자 로그아웃
    """
    await logout_user(
        db=db,
        response=response,
        user_id=current_user.user_id,
        refresh_token=refresh_token,
    )
    return LogoutResponse()


# 액세스 토큰 갱신
@router.post(
    "/token/refresh",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="액세스 토큰 갱신",
    responses=create_responses(
        AuthErrors.INVALID_TOKEN,
        AuthErrors.INVALID_TOKEN_PAYLOAD,
        AuthErrors.USER_NOT_ACTIVE,
        AuthErrors.USER_NOT_FOUND,
        AuthErrors.REFRESH_TOKEN_EXPIRED,
    ),
)
async def refresh_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
    refresh_user: Annotated[AuthenticatedUser, Depends(authenticate_refresh_token)],
) -> LoginResponse:
    """
    액세스 토큰 갱신
    """
    result = await refresh_access_token(
        db=db,
        response=response,
        user_id=refresh_user.user_id,
        email=refresh_user.email,
    )
    return result


# 내 정보 가져오기
@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="내 정보 가져오기",
)
async def get_me(
    db: Annotated[AsyncSession, Depends(get_db)],
    login_user: Annotated[AuthenticatedUser, Depends(registered_user)],
) -> UserResponse:
    """
    내 정보 가져오기
    """
    result = await get_user_info(
        db=db,
        user_id=login_user.user_id,
    )
    try:
        logger.info(f"[DEBUG] /me response: {result.model_dump_json()}")
    except Exception as e:
        logger.error(f"Failed to log /me response: {e}")
    return result
