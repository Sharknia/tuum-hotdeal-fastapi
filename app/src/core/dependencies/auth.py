from datetime import UTC, datetime, timedelta
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Cookie, Depends, Header, Response
from jose import ExpiredSignatureError, JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.config import settings
from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.repositories import (
    check_user_active,
    save_refresh_token,
    verify_refresh_token,
)
from app.src.domain.user.repositories import (
    delete_refresh_token as repo_delete_refresh_token,
)
from app.src.domain.user.schemas import AuthenticatedUser

ALGORITHM = "HS256"

# Annotated를 사용하여 DB 세션 의존성 타입 정의
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def create_access_token(
    user_id: UUID,
    email: str,
    nickname: str,
    auth_level: AuthLevel,
    expires_delta: timedelta | None = None,  # 만료 시간 인자 추가
) -> str:
    """
    Access Token 생성 함수
    """
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    payload = {
        "user_id": str(user_id),
        "email": email,
        "nickname": nickname,
        "auth_level": auth_level,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


async def create_refresh_token(
    db: AsyncSession,
    response: Response,
    user_id: UUID,
    email: str,
    expires_delta: timedelta = timedelta(days=7),
    user_agent: str | None = None,
) -> str:
    """
    Refresh Token 생성 함수
    - user_agent: 브라우저 User-Agent 헤더 (512자로 제한)
    """
    user_id_str = str(user_id)

    # User-Agent 길이 제한 (512자)
    if user_agent and len(user_agent) > 512:
        user_agent = user_agent[:512]

    payload = {
        "jti": str(uuid4()),  # JWT ID: 각 토큰에 고유 식별자 추가
        "user_id": user_id_str,
        "email": email,
        "exp": datetime.now(UTC) + expires_delta,
    }
    refresh_token = jwt.encode(
        payload, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM
    )
    await save_refresh_token(db, user_id, refresh_token, user_agent=user_agent)

    # 환경에 따라 secure, domain, samesite 속성 결정
    environment = settings.ENVIRONMENT
    cookie_domain = None
    is_secure = False
    samesite = "lax"

    if environment != "local":
        cookie_domain = ".tuum.day"
        is_secure = True
        samesite = "none"

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=is_secure,
        samesite=samesite,
        path="/",
        max_age=expires_delta.total_seconds(),
        domain=cookie_domain,
    )
    return refresh_token


async def delete_refresh_token(
    db: AsyncSession,
    response: Response,
    refresh_token: str | None = None,
) -> None:
    """현재 세션만 로그아웃합니다 (쿠키의 토큰 기반)."""
    if refresh_token:
        await repo_delete_refresh_token(db, refresh_token)

    # 환경에 따라 secure, domain, samesite 속성 결정 (쿠키 생성 시와 동일한 로직 사용)
    environment = getattr(settings, "ENVIRONMENT", "development")
    cookie_domain = None
    is_secure = False
    samesite = "lax"

    if environment in ["dev", "prod"]:
        cookie_domain = ".tuum.day"
        is_secure = True
        samesite = "None"

    response.delete_cookie(
        key="refresh_token",
        path="/",
        httponly=True,
        secure=is_secure,
        samesite=samesite,
        domain=cookie_domain,
    )
    return None


# ---- Internal Helper Functions for Authentication ----


async def _get_authenticated_user_from_token(token: str) -> AuthenticatedUser:
    """Helper to decode and validate the access token payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str: str = payload.get("user_id")
        email: str = payload.get("email")
        nickname: str = payload.get("nickname")
        auth_level_value: int = payload.get("auth_level")

        if (
            user_id_str is None
            or email is None
            or nickname is None
            or auth_level_value is None
        ):
            raise AuthErrors.INVALID_TOKEN_PAYLOAD

        try:
            # Validate UUID format
            UUID(user_id_str)
        except ValueError as e:
            raise AuthErrors.INVALID_TOKEN_PAYLOAD from e

        try:
            auth_level = AuthLevel(auth_level_value)
        except ValueError as e:
            raise AuthErrors.INVALID_TOKEN_PAYLOAD from e

        return AuthenticatedUser(
            user_id=user_id_str, email=email, nickname=nickname, auth_level=auth_level
        )
    except ExpiredSignatureError as e:
        raise AuthErrors.ACCESS_TOKEN_EXPIRED from e
    except JWTError as e:
        raise AuthErrors.INVALID_TOKEN from e


async def _validate_user_status_and_level(
    db: DBSession, user: AuthenticatedUser, required_level: AuthLevel
):
    """Helper to check if a user is active and has the required auth level."""
    user_uuid = user.user_id

    is_active_user = await check_user_active(db, user_uuid)
    if not is_active_user:
        raise AuthErrors.USER_NOT_ACTIVE

    if user.auth_level.value < required_level.value:
        raise AuthErrors.INSUFFICIENT_PERMISSIONS


# ---- Public Authentication Dependencies ----


async def registered_user(
    authorization: str = Header(None),
) -> AuthenticatedUser:
    """
    사용자 가입 의존성 함수 : 단순 가입만 확인 (DB 조회 없음)
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthErrors.INVALID_TOKEN

    token = authorization.split(" ")[1]
    return await _get_authenticated_user_from_token(token)


# 쿠키에 담겨온 리프레시 토큰 검증
async def authenticate_refresh_token(
    db: DBSession,
    response: Response,
    refresh_token: str = Cookie(None),
) -> AuthenticatedUser:
    """
    리프레시 토큰 검증 함수
    """
    if not refresh_token:
        raise AuthErrors.INVALID_TOKEN
    token = refresh_token
    try:
        # 토큰 검증 및 디코딩
        payload = jwt.decode(
            token, settings.REFRESH_TOKEN_SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id = payload.get("user_id")
        email: str = payload.get("email")

        if user_id is None or email is None:
            raise AuthErrors.INVALID_TOKEN_PAYLOAD

        # db에 저장된 리프레시 토큰과 비교
        try:
            user = await verify_refresh_token(db, token)
            if not user:
                raise AuthErrors.INVALID_TOKEN
        except ValueError as e:
            raise AuthErrors.INVALID_TOKEN from e

        # 인증된 사용자 정보 반환
        return AuthenticatedUser(
            user_id=user_id,
            email=email,
            nickname=user.nickname,
            auth_level=AuthLevel.USER,
        )

    except ExpiredSignatureError as e:
        raise AuthErrors.REFRESH_TOKEN_EXPIRED from e
    except JWTError as e:
        raise AuthErrors.INVALID_TOKEN from e


async def authenticate_user(
    db: DBSession,
    authorization: str = Header(None),
) -> AuthenticatedUser:
    """
    사용자 인증 의존성 함수 : 활성 상태인 일반 사용자(USER 레벨 이상) 확인
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthErrors.NOT_AUTHENTICATED

    token = authorization.split(" ")[1]

    authenticated_user = await _get_authenticated_user_from_token(token)
    await _validate_user_status_and_level(db, authenticated_user, AuthLevel.USER)

    return authenticated_user


# ---- 관리자 인증 함수 추가 ----
async def authenticate_admin_user(
    db: DBSession,
    authorization: str = Header(None),
) -> AuthenticatedUser:
    """
    관리자 인증 의존성 함수 : 활성 상태인 관리자(ADMIN 레벨 이상) 확인
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthErrors.NOT_AUTHENTICATED

    token = authorization.split(" ")[1]

    authenticated_user = await _get_authenticated_user_from_token(token)
    await _validate_user_status_and_level(db, authenticated_user, AuthLevel.ADMIN)

    return authenticated_user


async def create_password_reset_token(
    user_id: int,
) -> str:
    """
    비밀번호 재설정을 위한 JWT 생성
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.now(UTC) + timedelta(minutes=5),
        "purpose": "password_reset",
    }
    return jwt.encode(payload, settings.PASSWORD_SECRET_KEY, algorithm=ALGORITHM)


async def verify_password_reset_token(
    token: str,
) -> int:
    """
    비밀번호 재설정 JWT 검증
    """
    try:
        payload = jwt.decode(
            token, settings.PASSWORD_SECRET_KEY, algorithms=[ALGORITHM]
        )
        user_id: int = payload.get("user_id")
        purpose: str = payload.get("purpose")

        if user_id is None or purpose != "password_reset":
            raise AuthErrors.INVALID_TOKEN

        return user_id
    except ExpiredSignatureError as e:
        raise AuthErrors.ACCESS_TOKEN_EXPIRED from e
    except JWTError as e:
        raise AuthErrors.INVALID_TOKEN from e
