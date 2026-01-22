from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.exceptions.base_exceptions import BaseHTTPException
from app.src.core.exceptions.client_exceptions import ClientErrors
from app.src.domain.hotdeal.repositories import is_my_keyword
from app.src.domain.hotdeal.schemas import KeywordResponse
from app.src.domain.hotdeal.services import (
    register_keyword,
    unlink_keyword,
    view_users_keywords,
)
from app.src.domain.hotdeal.utils import normalize_keyword


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "title, user_id, expected_exception",
    [
        # 정상 케이스
        (
            "Keyword",
            "00000000-0000-0000-0000-00000000000a",
            None,
        ),
        # 키워드 추가 불가
        (
            "Keyword",
            "00000000-0000-0000-0000-00000000000a",
            ClientErrors.KEYWORD_COUNT_OVERFLOW,
        ),
    ],
)
async def test_register_keyword(
    add_mock_user,
    mock_db_session: AsyncSession,
    title,
    user_id,
    expected_exception: BaseHTTPException | None,
):
    """키워드 등록 서비스 테스트"""
    await add_mock_user(
        id=UUID("00000000-0000-0000-0000-00000000000a"),
        is_active=True,
        nickname="test_user",
        password="validpassword",
    )
    # 키워드 9개를 등록한다.
    for i in range(9):
        await register_keyword(
            db=mock_db_session,
            title=f"Keyword{i}",
            user_id=UUID("00000000-0000-0000-0000-00000000000a"),
        )

    if expected_exception:
        # 하나 더 등록
        await register_keyword(
            db=mock_db_session,
            title="Keyword10",
            user_id=UUID("00000000-0000-0000-0000-00000000000a"),
        )
        try:
            await register_keyword(
                db=mock_db_session,
                title=title,
                user_id=UUID(user_id),
            )
        except BaseHTTPException as exc:
            assert exc.status_code == expected_exception.status_code
            assert exc.detail == expected_exception.detail
        else:
            pytest.fail("Expected exception was not raised.")
    else:
        result: KeywordResponse = await register_keyword(
            db=mock_db_session,
            title=title,
            user_id=UUID(user_id),
        )
        assert isinstance(result, KeywordResponse)
        assert result.title == normalize_keyword(title)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "keyword_id, user_id, expected_exception",
    [
        # 정상 케이스
        (
            1,
            "00000000-0000-0000-0000-00000000000a",
            None,
        ),
        # 키워드 존재하지 않음
        (
            1,
            "00000000-0000-0000-0000-00000000000a",
            ClientErrors.KEYWORD_NOT_FOUND,
        ),
    ],
)
async def test_unlink_keyword(
    add_mock_user,
    mock_db_session: AsyncSession,
    keyword_id,
    user_id,
    expected_exception: BaseHTTPException | None,
):
    """키워드 삭제 서비스 테스트"""
    await add_mock_user(
        id=UUID(user_id),
        is_active=True,
        nickname="test_user",
        password="validpassword",
    )

    if expected_exception:
        try:
            await unlink_keyword(
                db=mock_db_session,
                keyword_id=keyword_id,
                user_id=UUID(user_id),
            )
        except BaseHTTPException as exc:
            assert exc.status_code == expected_exception.status_code
            assert exc.detail == expected_exception.detail
        else:
            pytest.fail("Expected exception was not raised.")
    else:
        # 키워드 등록한다.
        new_keyword: KeywordResponse = await register_keyword(
            db=mock_db_session,
            title="Keyword",
            user_id=UUID(user_id),
        )
        # 키워드 삭제
        await unlink_keyword(
            db=mock_db_session,
            keyword_id=new_keyword.id,
            user_id=UUID(user_id),
        )
        # 키워드 삭제 후 키워드 존재 여부 확인
        result = await is_my_keyword(mock_db_session, UUID(user_id), new_keyword.id)
        assert not result


@pytest.mark.asyncio
async def test_view_users_keywords(
    add_mock_user,
    mock_db_session: AsyncSession,
):
    """유저의 키워드 리스트 조회 서비스 테스트"""
    await add_mock_user(
        id=UUID("00000000-0000-0000-0000-00000000000a"),
        is_active=True,
        nickname="test_user",
        password="validpassword",
    )
    # 키워드 등록
    await register_keyword(
        db=mock_db_session,
        title="Keyword",
        user_id=UUID("00000000-0000-0000-0000-00000000000a"),
    )
    # 키워드 리스트 조회
    result: list[KeywordResponse] = await view_users_keywords(
        db=mock_db_session,
        user_id=UUID("00000000-0000-0000-0000-00000000000a"),
    )
    assert len(result) == 1
    assert result[0].title == "keyword"


@pytest.mark.asyncio
async def test_register_keyword_unlimited_for_admin_user(
    add_mock_user,
    mock_db_session: AsyncSession,
):
    """zel@kakao.com 사용자는 키워드 10개 제한 없이 무제한 등록 가능"""
    # 특별 사용자 생성
    admin_user = await add_mock_user(
        id=UUID("00000000-0000-0000-0000-00000000000b"),
        email="zel@kakao.com",
        is_active=True,
        nickname="admin_user",
        password="validpassword",
    )

    # 15개 키워드 등록 시도 - 모두 성공해야 함
    for i in range(15):
        result = await register_keyword(
            db=mock_db_session,
            title=f"AdminKeyword{i}",
            user_id=admin_user.id,
        )
        assert isinstance(result, KeywordResponse)
        assert result.title == f"adminkeyword{i}"

    # 키워드 목록 확인
    keywords = await view_users_keywords(
        db=mock_db_session,
        user_id=admin_user.id,
    )
    assert len(keywords) == 15


@pytest.mark.asyncio
async def test_register_keyword_fails_when_user_not_found(
    mock_db_session: AsyncSession,
):
    """존재하지 않는 user_id로 키워드 등록 시 USER_NOT_FOUND 에러"""
    fake_user_id = UUID("99999999-9999-9999-9999-999999999999")

    with pytest.raises(BaseHTTPException) as exc_info:
        await register_keyword(
            db=mock_db_session,
            title="테스트키워드",
            user_id=fake_user_id,
        )

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "User not found"
