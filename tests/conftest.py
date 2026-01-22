from collections.abc import AsyncGenerator
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.src.core.database import Base
from app.src.core.dependencies.auth import (
    authenticate_refresh_token,
    authenticate_user,
    registered_user,
)
from app.src.core.dependencies.db_session import get_db
from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.core.exceptions.base_exceptions import BaseHTTPException
from app.src.core.security import hash_password
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.models import User
from app.src.domain.user.schemas import AuthenticatedUser

# SQLite 인메모리 데이터베이스 설정 (비동기)
# 참고: SQLite 비동기 드라이버 필요 (e.g., aiosqlite)
# poetry add aiosqlite 또는 pip install aiosqlite
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
engine = create_async_engine(
    ASYNC_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 비동기 세션 메이커 설정
# expire_on_commit=False 는 FastAPI에서 Depends(get_db) 패턴과 함께 사용할 때 권장됨
SessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def mock_db_session() -> AsyncGenerator[AsyncSession, None]:
    """비동기 AsyncSession 객체를 생성하는 픽스처"""

    # 테이블 초기화 및 재생성 (비동기 방식)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # 비동기 세션 시작
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()  # 성공 시 커밋 (선택적)
        except Exception:
            await session.rollback()  # 실패 시 롤백
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture
async def add_mock_user(mock_db_session: AsyncSession):
    async def _add_mock_user(
        id: UUID | None = None,
        email: str = "test@example.com",
        password: str = "password",
        nickname: str = "test_user",
        is_active: bool = False,
    ) -> User:
        """테스트를 위한 mock user를 DB에 추가하는 함수"""
        id = id or uuid4()
        hashed_password = hash_password(password)
        user = User(
            id=id,
            email=email,
            hashed_password=hashed_password,
            nickname=nickname,
            is_active=is_active,
        )
        mock_db_session.add(user)
        await mock_db_session.commit()
        return user

    return _add_mock_user


@pytest_asyncio.fixture
async def mock_client(
    mock_db_session: AsyncSession,
):
    """
    FastAPI TestClient와 동일한 DB 세션 및 Redis 클라이언트 공유
    """

    def override_get_db():
        yield mock_db_session

    # DB 의존성 오버라이드
    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    yield client

    # 오버라이드 초기화
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user_data():
    """User 모델 예시"""
    return {
        "id": "00000000-0000-0000-0000-00000000000a",
        "email": "test@example.com",
        "password": "hashed_password",
        "nickname": "test_user",
        "is_active": True,
        "created_at": "2024-12-31T12:00:00Z",
        "updated_at": "2024-12-31T12:00:00Z",
        "auth_level": AuthLevel.USER,
    }


# AuthenticatedUser 모델 예시
@pytest.fixture
def mock_authenticated_user():
    return AuthenticatedUser(
        user_id="00000000-0000-0000-0000-00000000000a",
        email="test@example.com",
        nickname="test_user",
        auth_level=AuthLevel.USER,
    )


@pytest.fixture
def mock_login_response():
    """로그인 성공 응답 데이터"""
    return {
        "access_token": "access_token_example",
        "user_id": "00000000-0000-0000-0000-00000000000a",
    }


@pytest.fixture
def override_authenticate_refresh_token(mock_client: TestClient):
    """
    FastAPI 의존성을 오버라이드하는 함수.
    테스트에서 필요에 따라 Mock 데이터를 설정 가능.
    """

    def _override(
        mock_authenticated_user: AuthenticatedUser = None,
        error: BaseHTTPException = None,
    ):
        # 정상 요청: mock_authenticated_user 반환
        if error is None:

            def mock_authenticate():
                return mock_authenticated_user

        # 에러 케이스: 지정된 에러를 raise
        else:

            def mock_authenticate():
                raise error

        # FastAPI 의존성 주입 오버라이드 설정
        mock_client.app.dependency_overrides[authenticate_refresh_token] = (
            mock_authenticate
        )

    # 테스트에서 사용할 오버라이드 함수 반환
    return _override


@pytest.fixture
def override_registered_user(mock_client: TestClient):
    """
    FastAPI 의존성을 오버라이드하는 함수
    """

    def _override(
        mock_authenticated_user=None,
        error=None,
    ):
        # 정상 요청: mock_authenticated_user 반환
        if error is None:

            def mock_registered():
                return mock_authenticated_user

        else:
            # 에러 발생
            def mock_registered():
                raise error

        # FastAPI 의존성 주입 오버라이드 설정
        mock_client.app.dependency_overrides[registered_user] = mock_registered

    # 오버라이드 함수 반환
    return _override


@pytest.fixture
def override_authenticate_user(mock_client: TestClient):
    """
    FastAPI 의존성을 오버라이드하는 함수.
    실제 유저 존재 여부까지 검증하는 경우
    """

    def _override(
        mock_authenticated_user: AuthenticatedUser = None,
        error: BaseHTTPException = None,
    ):
        # 정상 요청: mock_authenticated_user 반환
        # BaseHTTPException가 AuthErrors에러여야 에러를 raise 한다.
        if error is not None and not isinstance(error, AuthErrors):

            def mock_authenticate():
                raise error

        else:

            def mock_authenticate():
                return mock_authenticated_user

        # FastAPI 의존성 주입 오버라이드 설정
        mock_client.app.dependency_overrides[authenticate_user] = mock_authenticate

    # 테스트에서 사용할 오버라이드 함수 반환
    return _override
