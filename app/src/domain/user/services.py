from datetime import datetime
from uuid import UUID

from fastapi import Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.config import settings
from app.src.core.dependencies.auth import (
    create_access_token,
    create_refresh_token,
    delete_refresh_token,
)
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.core.logger import logger
from app.src.core.security import hash_password, verify_password
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.repositories import (
    create_user,
    delete_token_by_hash,
    get_user_by_email,
    get_user_by_id,
)
from app.src.domain.user.schemas import (
    LoginResponse,
    UserResponse,
)
from app.src.Infrastructure.mail.mail_manager import send_email


async def create_new_user(
    db: AsyncSession,
    email: str,
    nickname: str,
    password: str,
) -> UserResponse:
    """
    새로운 사용자를 생성
    - 이메일 중복 확인
    - 비밀번호 해싱
    - 사용자 생성 (is_active=False, auth_level=USER)
    """
    existing_user = await get_user_by_email(db, email=email)
    if existing_user:
        raise AuthErrors.EMAIL_ALREADY_REGISTERED

    hashed_pwd = hash_password(password)
    is_active = False
    if settings.ENVIRONMENT != "prod":
        is_active = True

    new_user = await create_user(
        db=db,
        nickname=nickname,
        email=email,
        hashed_password=hashed_pwd,
        auth_level=AuthLevel.USER,
        is_active=is_active,
    )

    return UserResponse.model_validate(new_user)


async def login_user(
    db: AsyncSession,
    response: Response,
    email: str,
    password: str,
    request: Request | None = None,
) -> LoginResponse:
    user = await get_user_by_email(db, email=email)
    if not user:
        raise AuthErrors.USER_NOT_FOUND

    if not verify_password(password, user.hashed_password):
        raise AuthErrors.INVALID_PASSWORD

    if not user.is_active:
        raise AuthErrors.USER_NOT_ACTIVE

    user_agent = request.headers.get("user-agent") if request else None

    await create_refresh_token(
        db=db,
        response=response,
        user_id=user.id,
        email=user.email,
        user_agent=user_agent,
    )

    # 마지막 로그인 시간 업데이트
    user.last_login = datetime.now()
    db.add(user)
    await db.commit()

    return LoginResponse(
        access_token=await create_access_token(
            user.id, user.email, user.nickname, user.auth_level
        ),
        user_id=str(user.id),
    )


async def logout_user(
    db: AsyncSession,
    response: Response,
    user_id: UUID,
    refresh_token: str | None = None,
) -> None:
    # 실제 있는 유저인지 확인
    user = await get_user_by_id(db, user_id)
    if not user:
        raise AuthErrors.USER_NOT_FOUND

    # 활성화 상태 확인
    if not user.is_active:
        raise AuthErrors.USER_NOT_ACTIVE

    # 액세스 토큰을 블랙리스트에 등록하는 로직은 생략
    await delete_refresh_token(db, response, refresh_token)
    return None


async def refresh_access_token(
    db: AsyncSession,
    response: Response,
    user_id: UUID,
    email: str,
    token_hash: str | None = None,
) -> LoginResponse:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise AuthErrors.USER_NOT_FOUND

    if not user.is_active:
        raise AuthErrors.USER_NOT_ACTIVE

    # RTR: 기존 토큰 삭제 (새 토큰 생성 전)
    if token_hash:
        await delete_token_by_hash(db, token_hash)

    access_token = await create_access_token(
        user_id=user_id,
        email=email,
        nickname=user.nickname,
        auth_level=user.auth_level,
    )
    await create_refresh_token(
        db=db,
        response=response,
        user_id=user_id,
        email=email,
    )

    return LoginResponse(
        access_token=access_token,
        user_id=str(user_id),
    )


async def get_user_info(
    db: AsyncSession,
    user_id: UUID,
) -> UserResponse:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise AuthErrors.USER_NOT_FOUND

    return UserResponse.model_validate(user)


async def send_new_user_notifications(admin_emails: list[str], user: UserResponse) -> None:
    subject = f"[Tuum] 신규 회원 가입: {user.nickname}"
    body = f"""새로운 회원이 가입했습니다.
이메일: {user.email}
닉네임: {user.nickname}
관리자: https://hotdeal.tuum.day/admin"""

    for email in admin_emails:
        try:
            await send_email(subject=subject, to=email, body=body)
        except Exception as e:
            logger.error(f"신규 가입 알림 메일 발송 중 오류 발생 ({email}): {e}")


async def send_approval_notification(email: str, nickname: str) -> None:
    """
    사용자 승인 알림 메일을 발송합니다.
    """
    subject = "[Tuum] 가입이 승인되었습니다"
    body = f"""안녕하세요, {nickname}님!

귀하의 가입이 승인되었습니다.
이제 서비스를 이용하실 수 있습니다.

로그인: https://hotdeal.tuum.day/login"""

    try:
        await send_email(subject=subject, to=email, body=body)
    except Exception as e:
        logger.error(f"승인 알림 메일 발송 중 오류 발생 ({email}): {e}")
