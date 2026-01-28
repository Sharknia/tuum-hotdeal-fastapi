"""다중 세션 인증 통합 테스트"""
import datetime as dt
from datetime import UTC, timedelta

import pytest
from fastapi import Response
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.core.config import settings
from app.src.domain.user.repositories import (
    delete_refresh_token as repo_delete_refresh_token,
)
from app.src.domain.user.repositories import (
    save_refresh_token,
    verify_refresh_token,
)
from app.src.domain.user.services import logout_user, refresh_access_token

ALGORITHM = "HS256"


@pytest.mark.asyncio
async def test_multi_device_login_success(
    add_mock_user,
    mock_db_session: AsyncSession,
):
    """
    테스트 케이스 1: A기기 로그인 -> B기기 로그인 -> 둘 다 인증 성공 확인

    다중 기기에서 동시에 로그인했을 때, 두 기기 모두 정상적으로 인증되는지 확인합니다.
    """
    user_a = await add_mock_user(
        email="device-a@example.com",
        password="securepassword",
        nickname="test_user_a",
        is_active=True,
    )

    user_b = await add_mock_user(
        email="device-b@example.com",
        password="securepassword",
        nickname="test_user_b",
        is_active=True,
    )

    now = dt.datetime.now(UTC)
    payload_a = {
        "user_id": str(user_a.id),
        "email": user_a.email,
        "exp": now + timedelta(days=7),
    }
    token_a = jwt.encode(payload_a, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    await save_refresh_token(mock_db_session, user_a.id, token_a, user_agent="Device-A-Browser")

    verified_user_a = await verify_refresh_token(mock_db_session, token_a)
    assert verified_user_a is not None
    assert verified_user_a.id == user_a.id

    payload_b = {
        "user_id": str(user_b.id),
        "email": user_b.email,
        "exp": now + timedelta(days=7),
    }
    token_b = jwt.encode(payload_b, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    await save_refresh_token(mock_db_session, user_b.id, token_b, user_agent="Device-B-Browser")

    verified_user_b = await verify_refresh_token(mock_db_session, token_b)
    assert verified_user_b is not None
    assert verified_user_b.id == user_b.id

    assert token_a != token_b
    verified_a_again = await verify_refresh_token(mock_db_session, token_a)
    verified_b_again = await verify_refresh_token(mock_db_session, token_b)
    assert verified_a_again is not None
    assert verified_b_again is not None


@pytest.mark.asyncio
async def test_fifo_session_limit(
    add_mock_user,
    mock_db_session: AsyncSession,
    monkeypatch,
):
    """
    테스트 케이스 2: 3개 기기 로그인 -> 1번째 기기 인증 실패 확인 (FIFO 동작)

    세션 제한(MAX_SESSIONS_PER_USER)을 2로 설정하고, 3번째 기기 로그인 시
    가장 오래된(1번째) 세션이 삭제되는 FIFO 동작을 확인합니다.
    """
    import app.src.domain.user.repositories as repo_module
    monkeypatch.setattr(repo_module, "MAX_SESSIONS_PER_USER", 2)

    user = await add_mock_user(
        email="test@example.com",
        password="securepassword",
        nickname="test_user",
        is_active=True,
    )

    now = dt.datetime.now(UTC)

    payload_1 = {
        "user_id": str(user.id),
        "email": user.email,
        "exp": now + timedelta(days=7),
    }
    token_1 = jwt.encode(payload_1, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    await save_refresh_token(mock_db_session, user.id, token_1, user_agent="Device-1-Browser")

    payload_2 = {
        "user_id": str(user.id),
        "email": user.email,
        "exp": now + timedelta(days=7, seconds=1),
    }
    token_2 = jwt.encode(payload_2, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    await save_refresh_token(mock_db_session, user.id, token_2, user_agent="Device-2-Browser")

    verified_1 = await verify_refresh_token(mock_db_session, token_1)
    verified_2 = await verify_refresh_token(mock_db_session, token_2)
    assert verified_1 is not None
    assert verified_2 is not None

    payload_3 = {
        "user_id": str(user.id),
        "email": user.email,
        "exp": now + timedelta(days=7, seconds=2),
    }
    token_3 = jwt.encode(payload_3, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    await save_refresh_token(mock_db_session, user.id, token_3, user_agent="Device-3-Browser")

    verified_1_after = await verify_refresh_token(mock_db_session, token_1)
    assert verified_1_after is None, "가장 오래된 세션이 삭제되어야 함"

    verified_2_after = await verify_refresh_token(mock_db_session, token_2)
    verified_3_after = await verify_refresh_token(mock_db_session, token_3)
    assert verified_2_after is not None, "두 번째 세션은 유지되어야 함"
    assert verified_3_after is not None, "새 세션이 추가되어야 함"

    from sqlalchemy import func, select

    from app.src.domain.user.models import RefreshToken

    result = await mock_db_session.execute(
        select(func.count())
        .select_from(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.expires_at > dt.datetime.now(UTC),
        )
    )
    active_session_count = result.scalar()
    assert active_session_count == 2, "활성 세션 수는 최대 2개여야 함"


@pytest.mark.asyncio
async def test_logout_token_reuse_failure(
    add_mock_user,
    mock_db_session: AsyncSession,
):
    """
    테스트 케이스 3: 로그아웃 후 해당 토큰 재사용 불가 확인

    로그아웃 후 해당 기기의 리프레시 토큰이 삭제되어 재사용 불가능한지 확인합니다.
    """
    user = await add_mock_user(
        email="logout-test@example.com",
        password="securepassword",
        nickname="test_user",
        is_active=True,
    )

    now = dt.datetime.now(UTC)

    payload = {
        "user_id": str(user.id),
        "email": user.email,
        "exp": now + timedelta(days=7),
    }
    token = jwt.encode(payload, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    await save_refresh_token(mock_db_session, user.id, token, user_agent="Test-Device-Browser")

    verified_before_logout = await verify_refresh_token(mock_db_session, token)
    assert verified_before_logout is not None, "로그인 후 토큰 검증에 성공해야 함"

    response_logout = Response()
    await logout_user(
        db=mock_db_session,
        response=response_logout,
        user_id=user.id,
        refresh_token=token,
    )

    verified_after_logout = await verify_refresh_token(mock_db_session, token)
    assert verified_after_logout is None, "로그아웃 후 토큰은 삭제되어 재사용 불가해야 함"

    user_2 = await add_mock_user(
        email="logout-test-2@example.com",
        password="securepassword",
        nickname="test_user_2",
        is_active=True,
    )

    payload_2 = {
        "user_id": str(user_2.id),
        "email": user_2.email,
        "exp": now + timedelta(days=7, seconds=1),
    }
    token_2 = jwt.encode(payload_2, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    await save_refresh_token(mock_db_session, user_2.id, token_2, user_agent="Test-Device-Browser")

    verified_2_before = await verify_refresh_token(mock_db_session, token_2)
    assert verified_2_before is not None

    await repo_delete_refresh_token(mock_db_session, token_2)

    verified_2_after = await verify_refresh_token(mock_db_session, token_2)
    assert verified_2_after is None, "토큰 삭제 후 검증에 실패해야 함"


@pytest.mark.asyncio
async def test_multiple_sessions_different_devices(
    add_mock_user,
    mock_db_session: AsyncSession,
    monkeypatch,
):
    """
    추가 테스트: 여러 기기에서 로그인했을 때 각 기기의 토큰이 독립적으로 동작하는지 확인

    세션 제한(MAX_SESSIONS_PER_USER)을 2로 설정하고, 각 기기가 독립적으로
    로그아웃 가능한지 확인합니다.
    """
    import app.src.domain.user.repositories as repo_module
    monkeypatch.setattr(repo_module, "MAX_SESSIONS_PER_USER", 2)

    user_a = await add_mock_user(
        email="multi-device-a@example.com",
        password="securepassword",
        nickname="test_user_a",
        is_active=True,
    )

    user_b = await add_mock_user(
        email="multi-device-b@example.com",
        password="securepassword",
        nickname="test_user_b",
        is_active=True,
    )

    now = dt.datetime.now(UTC)

    payload_a = {
        "user_id": str(user_a.id),
        "email": user_a.email,
        "exp": now + timedelta(days=7),
    }
    token_a = jwt.encode(payload_a, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    await save_refresh_token(mock_db_session, user_a.id, token_a, user_agent="Device-A")

    payload_b = {
        "user_id": str(user_b.id),
        "email": user_b.email,
        "exp": now + timedelta(days=7, seconds=1),
    }
    token_b = jwt.encode(payload_b, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    await save_refresh_token(mock_db_session, user_b.id, token_b, user_agent="Device-B")

    assert await verify_refresh_token(mock_db_session, token_a) is not None
    assert await verify_refresh_token(mock_db_session, token_b) is not None

    response_logout_a = Response()
    await logout_user(
        db=mock_db_session,
        response=response_logout_a,
        user_id=user_a.id,
        refresh_token=token_a,
    )

    assert await verify_refresh_token(mock_db_session, token_a) is None, "A기기 로그아웃 후 토큰 삭제 확인"
    assert await verify_refresh_token(mock_db_session, token_b) is not None, "B기기 토큰 유지 확인"

    response_logout_b = Response()
    await logout_user(
        db=mock_db_session,
        response=response_logout_b,
        user_id=user_b.id,
        refresh_token=token_b,
    )

    assert await verify_refresh_token(mock_db_session, token_b) is None, "B기기 로그아웃 후 토큰 삭제 확인"


@pytest.mark.asyncio
async def test_refresh_token_rotation(
    add_mock_user,
    mock_db_session: AsyncSession,
):
    """
    테스트 케이스: 토큰 갱신 후 기존 토큰 재사용 불가 (RTR)

    토큰 갱신 시 기존 토큰이 삭제되어 재사용 불가능한지 확인합니다.
    """
    from app.src.core.security import get_token_hash

    # 1. 사용자 생성
    user = await add_mock_user(
        email="rtr-test@example.com",
        password="securepassword",
        nickname="test_user",
        is_active=True,
    )

    now = dt.datetime.now(UTC)

    # 2. 초기 토큰 A 발급
    payload_a = {
        "user_id": str(user.id),
        "email": user.email,
        "exp": now + timedelta(days=7),
    }
    token_a = jwt.encode(payload_a, settings.REFRESH_TOKEN_SECRET_KEY, algorithm=ALGORITHM)
    await save_refresh_token(mock_db_session, user.id, token_a, user_agent="Test-Device")

    # 토큰 A 검증 확인
    verified_user_a = await verify_refresh_token(mock_db_session, token_a)
    assert verified_user_a is not None, "초기 토큰 A 검증에 성공해야 함"
    assert verified_user_a.id == user.id

    # 3. 토큰 A 갱신 (토큰 A -> 토큰 B)
    token_a_hash = get_token_hash(token_a)
    response = Response()
    await refresh_access_token(
        db=mock_db_session,
        response=response,
        user_id=user.id,
        email=user.email,
        token_hash=token_a_hash,
    )

    # 새로 발급된 리프레시 토큰을 쿠키에서 추출
    token_b = None
    for header_name, header_value in response.headers.items():
        if header_name.lower() == "set-cookie" and "refresh_token=" in header_value:
            token_b = header_value.split("refresh_token=")[1].split(";")[0]
            break

    assert token_b is not None, "새로운 리프레시 토큰이 발급되어야 함"
    assert token_a != token_b, "토큰이 변경되어야 함"

    # 4. 토큰 A는 삭제되었는지 확인
    verified_user_a_after = await verify_refresh_token(mock_db_session, token_a)
    assert verified_user_a_after is None, "토큰 A는 삭제되어 재사용 불가해야 함"

    # 5. 토큰 B는 유효한지 확인
    verified_user_b = await verify_refresh_token(mock_db_session, token_b)
    assert verified_user_b is not None, "새 토큰 B는 유효해야 함"
    assert verified_user_b.id == user.id
