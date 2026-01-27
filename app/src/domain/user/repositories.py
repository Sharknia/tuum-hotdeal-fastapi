from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .enums import AuthLevel
from .models import User


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
) -> None:
    """사용자의 리프레시 토큰을 저장합니다."""
    stmt = update(User).where(User.id == user_id).values(refresh_token=token)
    await db.execute(stmt)
    await db.commit()


async def verify_refresh_token(
    db: AsyncSession,
    user_id: UUID,
    token: str,
) -> User | None:
    """제공된 리프레시 토큰이 저장된 토큰과 일치하는지 확인합니다."""
    result = await db.execute(
        select(User).where(User.id == user_id).where(User.refresh_token == token)
    )
    user: User | None = result.scalar_one_or_none()
    return user


async def init_refresh_token(
    db: AsyncSession,
    user_id: UUID,
) -> None:
    """사용자의 리프레시 토큰을 초기화합니다 (None으로 설정)."""
    stmt = update(User).where(User.id == user_id).values(refresh_token=None)
    await db.execute(stmt)
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
