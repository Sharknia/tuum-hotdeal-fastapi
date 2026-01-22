from uuid import UUID

from sqlalchemy import delete, func, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import exists

from app.src.domain.hotdeal.models import Keyword
from app.src.domain.user.models import User, user_keywords


# 새로운 키워드 등록
async def create_keyword(
    db: AsyncSession,
    title: str,
) -> Keyword:
    new_keyword = Keyword(title=title)
    db.add(new_keyword)
    await db.commit()
    await db.refresh(new_keyword)
    return new_keyword


# title을 받아서 키워드 조회
async def get_keyword_by_title(
    db: AsyncSession,
    title: str,
) -> Keyword | None:
    result = await db.execute(select(Keyword).filter(Keyword.title == title))
    return result.scalar_one_or_none()


# 내 키워드 갯수 확인
async def get_my_keyword_count(
    db: AsyncSession,
    user_id: UUID,
) -> int:
    result = await db.execute(
        select(func.count(Keyword.id)).filter(Keyword.users.any(User.id == user_id))
    )
    return result.scalar_one_or_none()


# 내 키워드 추가
async def add_my_keyword(
    db: AsyncSession,
    user_id: UUID,
    keyword_id: int,
) -> None:
    # 해당 키워드가 사용자의 키워드인지 먼저 확인
    is_already_added = await is_my_keyword(db, user_id, keyword_id)
    if is_already_added:
        raise ValueError("이미 등록된 키워드입니다.")

    insert_query = insert(user_keywords).values(user_id=user_id, keyword_id=keyword_id)
    await db.execute(insert_query)
    await db.commit()


# 내가 가지고 있는 키워드인지 조회
async def is_my_keyword(
    db: AsyncSession,
    user_id: UUID,
    keyword_id: int,
) -> bool:
    exists_query = select(
        exists().where(
            (user_keywords.c.user_id == user_id)
            & (user_keywords.c.keyword_id == keyword_id)
        )
    )
    result = await db.execute(exists_query)
    return result.scalar()


# 내 키워드 연결 끊기
async def unlink_user_keyword(
    db: AsyncSession,
    user_id: UUID,
    keyword_id: int,
) -> None:
    delete_query = delete(user_keywords).where(
        (user_keywords.c.user_id == user_id)
        & (user_keywords.c.keyword_id == keyword_id)
    )
    await db.execute(delete_query)
    await db.commit()


# 키워드가 사용중인지 확인
async def is_keyword_used(
    db: AsyncSession,
    keyword_id: int,
) -> bool:
    exists_query = select(exists().where(user_keywords.c.keyword_id == keyword_id))
    result = await db.execute(exists_query)
    return result.scalar()


# 키워드 삭제
async def delete_keyword(
    db: AsyncSession,
    keyword_id: int,
) -> None:
    delete_query = delete(Keyword).where(Keyword.id == keyword_id)
    await db.execute(delete_query)
    await db.commit()


# 유저의 키워드 리스트 조회 (이름으로 정렬)
async def select_users_keywords(
    db: AsyncSession,
    user_id: UUID,
) -> list[Keyword]:
    select_query = (
        select(Keyword)
        .where(Keyword.users.any(User.id == user_id))
        .order_by(Keyword.title)
    )
    result = await db.execute(select_query)
    return result.scalars().all()
