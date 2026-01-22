import asyncio
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.exceptions.client_exceptions import ClientErrors
from app.src.domain.hotdeal.models import Keyword
from app.src.domain.hotdeal.repositories import (
    add_my_keyword,
    create_keyword,
    delete_keyword,
    get_keyword_by_title,
    get_my_keyword_count,
    is_keyword_used,
    is_my_keyword,
    select_users_keywords,
    unlink_user_keyword,
)
from app.src.domain.hotdeal.schemas import KeywordResponse
from app.src.domain.hotdeal.utils import normalize_keyword
from app.src.domain.user.repositories import get_user_by_id
from app.src.Infrastructure.mail.mail_manager import send_email

router = APIRouter(prefix="/v1", tags=["hotdeal"])


async def register_keyword(
    db: AsyncSession,
    title: str,
    user_id: UUID,
) -> KeywordResponse:
    # 키워드에서 공백 제거하고 소문자로 변환
    title = normalize_keyword(title)
    if len(title) == 0:
        raise ClientErrors.INVALID_KEYWORD_TITLE
    # 이미 존재하는 키워드인지 확인
    keyword: Keyword | None = await get_keyword_by_title(db, title)
    # 존재하지 않을 경우 키워드 등록
    if keyword is None:
        keyword = await create_keyword(db, title)
    # 내 키워드 갯수 확인, 지금 이미 10개라면 추가 불가
    my_keyword_count: int = await get_my_keyword_count(db, user_id)
    if my_keyword_count >= 10:
        raise ClientErrors.KEYWORD_COUNT_OVERFLOW
    # 내 키워드로 등록
    try:
        await add_my_keyword(db, user_id, keyword.id)
    except:
        raise ClientErrors.DUPLICATE_KEYWORD_REGISTRATION

    # --- 백그라운드에서 이메일 발송 ---
    user = await get_user_by_id(db, user_id)
    if user:
        subject = f"'{title}' 키워드가 등록되었습니다."
        body = f"""
        <html>
        <body>
            <h2>키워드 등록이 완료되었습니다.</h2>
            <p>안녕하세요, {user.nickname}님.</p>
            <p>요청하신 키워드 '<b>{title}</b>'이(가) 성공적으로 등록되었습니다.</p>
            <p>이제부터 '{title}'에 대한 새로운 핫딜을 찾아 알려드릴게요.</p>
            <br>
            <hr>
            <p><small>본 메일은 발신전용입니다.</small></p>
        </body>
        </html>
        """
        asyncio.create_task(
            send_email(subject=subject, to=user.email, body=body, is_html=True)
        )

    return KeywordResponse(
        id=keyword.id,
        title=keyword.title,
    )


async def unlink_keyword(
    db: AsyncSession,
    keyword_id: int,
    user_id: UUID,
) -> None:
    # 내가 해당 키워드를 가지고 있는지 확인
    has_keyword: bool = await is_my_keyword(db, user_id, keyword_id)
    if not has_keyword:
        raise ClientErrors.KEYWORD_NOT_FOUND
    # 가지고 있다면 연결을 끊는다.
    await unlink_user_keyword(db, user_id, keyword_id)
    # 연결을 끊은 후 해당 키워드를 가지고 있는 사람이 있는지 확인
    is_used: bool = await is_keyword_used(db, keyword_id)
    # 사람이 없다면 키워드를 삭제한다.
    if not is_used:
        await delete_keyword(db, keyword_id)
    return


async def view_users_keywords(
    db: AsyncSession,
    user_id: UUID,
) -> list[KeywordResponse]:
    # 유저의 키워드 리스트 조회
    keywords: list[Keyword] = await select_users_keywords(db, user_id)
    return [KeywordResponse(id=keyword.id, title=keyword.title) for keyword in keywords]
