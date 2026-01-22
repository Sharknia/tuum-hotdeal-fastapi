from uuid import UUID

import pytest
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.core.exceptions.base_exceptions import BaseHTTPException
from app.src.domain.user.models import User
from app.src.domain.user.schemas import (
    LoginResponse,
    UserResponse,
)
from app.src.domain.user.services import (
    create_new_user,
    get_user_info,
    login_user,
    refresh_access_token,
)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password, nickname, expected_exception",
    [
        # 정상 케이스
        (
            "test@example.com",
            "securepassword",
            "test_user",
            None,
        ),
        # 이메일 중복
        (
            "duplicate@example.com",
            "securepassword",
            "duplicate_user",
            AuthErrors.EMAIL_ALREADY_REGISTERED,
        ),
    ],
)
async def test_create_new_user(
    add_mock_user,
    mock_db_session: AsyncSession,
    email,
    password,
    nickname,
    expected_exception: BaseHTTPException | None,
):
    """회원가입 서비스 테스트"""
    # 중복 검사를 위한 기존 유저 추가
    user: User = await add_mock_user(
        email="duplicate@example.com",
        password="password123",
        nickname="duplicate_user",
        is_active=True,
    )

    if expected_exception:
        try:
            await create_new_user(
                db=mock_db_session,
                email=email,
                password=password,
                nickname=nickname,
            )
        except BaseHTTPException as exc:
            assert exc.status_code == expected_exception.status_code
            assert exc.detail == expected_exception.detail
        else:
            pytest.fail("Expected exception was not raised.")
    else:
        result: UserResponse = await create_new_user(
            db=mock_db_session,
            email=email,
            password=password,
            nickname=nickname,
        )
        assert isinstance(result, UserResponse)
        assert result.email == email


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "email, password, is_active, expected_exception",
    [
        # 정상 케이스
        (
            "test@example.com",
            "securepassword",
            True,
            None,
        ),
        # 이메일 미등록
        (
            "nonexistent@example.com",
            "securepassword",
            True,
            AuthErrors.USER_NOT_FOUND,
        ),
        # 비밀번호 불일치
        (
            "test@example.com",
            "wrongpassword",
            True,
            AuthErrors.INVALID_PASSWORD,
        ),
        # 활성화 유저가 아님
        (
            "test@example.com",
            "securepassword",
            False,
            AuthErrors.USER_NOT_ACTIVE,
        ),
    ],
)
async def test_login_user(
    add_mock_user,
    mock_db_session: AsyncSession,
    email,
    password,
    is_active,
    expected_exception: BaseHTTPException | None,
):
    """로그인 서비스 테스트"""
    # 정상 로그인 테스트를 위한 유저 추가
    user: User = await add_mock_user(
        email="test@example.com",
        password="securepassword",
        nickname="test_user",
        is_active=is_active,
    )
    response = Response()
    if expected_exception:
        try:
            await login_user(
                db=mock_db_session,
                response=response,
                email=email,
                password=password,
            )
        except BaseHTTPException as exc:
            assert exc.status_code == expected_exception.status_code
            assert exc.detail == expected_exception.detail
        else:
            pytest.fail(f"Expected exception was not raised: {expected_exception}")
    else:
        result: LoginResponse = await login_user(
            db=mock_db_session,
            response=response,
            email=email,
            password=password,
        )
        assert isinstance(result, LoginResponse)
        assert result.access_token is not None
        assert result.user_id == str(user.id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id, email, expected_exception",
    [
        # 정상 케이스
        (
            "00000000-0000-0000-0000-00000000000a",
            "test@example.com",
            None,
        ),
        # 잘못된 사용자 ID
        (
            "00000000-0000-0000-0000-00000000000b",
            "test@example.com",
            AuthErrors.USER_NOT_FOUND,
        ),
        # 잘못된 이메일
        (
            "00000000-0000-0000-0000-00000000000b",
            "invalidemail@example.com",
            AuthErrors.USER_NOT_FOUND,
        ),
    ],
)
async def test_refresh_access_token(
    add_mock_user,
    mock_db_session: AsyncSession,
    user_id,
    email,
    expected_exception: BaseHTTPException,
):
    """액세스 토큰 갱신 서비스 테스트"""
    response = Response()
    # 테스트를 위한 초기 데이터 추가
    if email == "test@example.com":
        user: User = await add_mock_user(
            id=UUID("00000000-0000-0000-0000-00000000000a"),
            is_active=True,
            nickname="test_user",
            password="validpassword",
        )

    if expected_exception:
        try:
            await refresh_access_token(
                db=mock_db_session,
                response=response,
                user_id=UUID(user_id),
                email=email,
            )
        except BaseHTTPException as exc:
            assert exc.status_code == expected_exception.status_code
            assert exc.detail == expected_exception.detail
        else:
            pytest.fail("Expected exception was not raised.")
    else:
        result: LoginResponse = await refresh_access_token(
            db=mock_db_session,
            response=response,
            user_id=UUID(user_id),
            email=email,
        )
        assert isinstance(result, LoginResponse)
        assert result.access_token is not None
        assert result.user_id == user_id


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "user_id, expected_exception",
    [
        # 정상 케이스
        (
            "00000000-0000-0000-0000-00000000000a",
            None,
        ),
        # 잘못된 사용자 ID
        (
            "00000000-0000-0000-0000-00000000000b",
            AuthErrors.USER_NOT_FOUND,
        ),
    ],
)
async def test_get_user_info(
    add_mock_user,
    mock_db_session: AsyncSession,
    user_id,
    expected_exception: BaseHTTPException,
):
    """내 정보 가져오기 서비스 테스트"""

    user: User = await add_mock_user(
        id=UUID("00000000-0000-0000-0000-00000000000a"),
        is_active=True,
        nickname="test_user",
        password="validpassword",
    )

    if expected_exception:
        try:
            await get_user_info(
                db=mock_db_session,
                user_id=UUID(user_id),
            )
        except BaseHTTPException as exc:
            assert exc.status_code == expected_exception.status_code
            assert exc.detail == expected_exception.detail
        else:
            pytest.fail("Expected exception was not raised.")
    else:
        result: UserResponse = await get_user_info(
            db=mock_db_session,
            user_id=UUID(user_id),
        )
        assert isinstance(result, UserResponse)
        assert result.email == user.email
        assert result.nickname == user.nickname
        assert result.is_active == user.is_active
        assert result.auth_level == user.auth_level
