from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.src.core.security import get_token_hash

from .enums import AuthLevel
from .models import RefreshToken, User

MAX_SESSIONS_PER_USER = 5


async def create_user(
    db: AsyncSession,
    nickname: str,
    email: str,
    hashed_password: str,
    auth_level: AuthLevel = AuthLevel.USER,
    is_active: bool = False,
) -> User:
    """새로운 사용자를 생성합니다."""
    new_user = User(
        nickname=nickname,
        email=email,
        hashed_password=hashed_password,
        auth_level=auth_level,
        is_active=is_active,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def get_user_by_nickname(
    db: AsyncSession,
    nickname: str,
) -> User | None:
    """닉네임으로 사용자를 조회합니다."""
    result = await db.execute(select(User).filter(User.nickname == nickname))
    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession,
    email: str,
) -> User | None:
    """이메일로 사용자를 조회합니다."""
    result = await db.execute(select(User).filter(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(
    db: AsyncSession,
    user_id: UUID,
) -> User | None:
    """UUID로 사용자를 조회합니다."""
    result = await db.execute(select(User).filter(User.id == user_id))
    return result.scalar_one_or_none()


async def activate_user(
    db: AsyncSession,
    user_id: UUID,
) -> User | None:
    """사용자를 활성화합니다 (is_active = True)."""
    user = await get_user_by_id(db, user_id)
    if user and not user.is_active:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_active=True)
            .returning(User)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()
    return user


async def deactivate_user(
    db: AsyncSession,
    user_id: UUID,
) -> User | None:
    """사용자를 비활성화합니다 (is_active = False)."""
    user = await get_user_by_id(db, user_id)
    if user and user.is_active:
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(is_active=False)
            .returning(User)
        )
        result = await db.execute(stmt)
        await db.commit()
        return result.scalar_one_or_none()
    return user


async def get_user_with_keywords(
    db: AsyncSession,
    user_id: UUID,
) -> User | None:
    """사용자와 해당 사용자의 키워드 목록을 함께 조회합니다."""
    result = await db.execute(
        select(User).filter(User.id == user_id).options(selectinload(User.keywords))
    )
    return result.scalar_one_or_none()


async def update_user_auth_level(
    db: AsyncSession,
    user_id: UUID,
    new_level: AuthLevel,
) -> User | None:
    """사용자의 권한 레벨을 변경합니다."""
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(auth_level=new_level)
        .returning(User)
    )
    result = await db.execute(stmt)
    updated_user = result.scalar_one_or_none()
    if updated_user:
        await db.commit()
        return updated_user
    return None


async def update_user_password(
    db: AsyncSession,
    user_id: UUID,
    new_hashed_password: str,
) -> User | None:
    """사용자의 비밀번호를 업데이트합니다."""
    stmt = (
        update(User)
        .where(User.id == user_id)
        .values(hashed_password=new_hashed_password)
        .returning(User)
    )
    result = await db.execute(stmt)
    updated_user = result.scalar_one_or_none()
    if updated_user:
        await db.commit()
        return updated_user
    return None


async def get_inactive_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """비활성 사용자 목록을 조회합니다."""
    result = await db.execute(
        select(User).filter(~User.is_active).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_all_users(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """모든 사용자 목록을 조회합니다."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_user_auth_level(
    db: AsyncSession,
    user_id: UUID,
) -> AuthLevel | None:
    """사용자의 권한 레벨을 조회합니다."""
    result = await db.execute(select(User.auth_level).filter(User.id == user_id))
    auth_level_value = result.scalar_one_or_none()
    if auth_level_value is not None:
        return AuthLevel(auth_level_value)  # int를 Enum으로 변환
    return None


async def save_refresh_token(
    db: AsyncSession,
    user_id: UUID,
    token: str,
    expires_delta: timedelta = timedelta(days=7),
    user_agent: str | None = None,
) -> None:
    """새 리프레시 토큰을 저장합니다. (만료토큰 정리 + 세션 제한 적용)"""
    now = datetime.now(UTC)
    expires_at = now + expires_delta

    await db.execute(
        delete(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at < now,
        )
    )

    result = await db.execute(
        select(func.count())
        .select_from(RefreshToken)
        .where(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at > now,
        )
    )
    active_session_count = result.scalar() or 0

    if active_session_count >= MAX_SESSIONS_PER_USER:
        oldest_token = await db.execute(
            select(RefreshToken.id)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.expires_at > now,
            )
            .order_by(RefreshToken.created_at.asc())
            .limit(1)
        )
        oldest_id = oldest_token.scalar()
        if oldest_id:
            await db.execute(delete(RefreshToken).where(RefreshToken.id == oldest_id))

    token_hash = get_token_hash(token)
    new_refresh_token = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        user_agent=user_agent,
        expires_at=expires_at,
    )
    db.add(new_refresh_token)
    await db.commit()


async def verify_refresh_token(
    db: AsyncSession,
    token: str,
) -> User | None:
    """리프레시 토큰을 검증하고 해당 사용자를 반환합니다."""
    token_hash = get_token_hash(token)
    now = datetime.now(UTC)

    result = await db.execute(
        select(RefreshToken)
        .where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.expires_at > now,
        )
        .options(selectinload(RefreshToken.user))
    )
    refresh_token = result.scalar_one_or_none()

    if refresh_token is None:
        return None

    return refresh_token.user


async def delete_refresh_token(
    db: AsyncSession,
    token: str,
) -> None:
    """특정 리프레시 토큰을 삭제합니다 (로그아웃)."""
    token_hash = get_token_hash(token)
    await db.execute(delete(RefreshToken).where(RefreshToken.token_hash == token_hash))
    await db.commit()


async def delete_all_user_tokens(
    db: AsyncSession,
    user_id: UUID,
) -> None:
    """특정 사용자의 모든 리프레시 토큰을 삭제합니다 (전체 로그아웃)."""
    await db.execute(delete(RefreshToken).where(RefreshToken.user_id == user_id))
    await db.commit()


async def check_user_active(
    db: AsyncSession,
    user_id: UUID,
) -> bool:
    """사용자의 활성 상태(is_active)를 확인합니다."""
    result = await db.execute(select(User.is_active).where(User.id == user_id))
    is_active = result.scalar_one_or_none()
    if is_active is None:
        return False
    return is_active


async def get_all_admins(db: AsyncSession) -> list[str]:
    """관리자 권한을 가진 모든 사용자의 이메일 목록을 조회합니다."""
    result = await db.execute(select(User.email).where(User.auth_level == AuthLevel.ADMIN))
    return list(result.scalars().all())
