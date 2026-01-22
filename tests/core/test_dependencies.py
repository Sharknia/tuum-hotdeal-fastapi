from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

# 테스트 대상 함수 및 객체 임포트 경로 수정
from app.src.core.dependencies.db_session import get_db


@pytest.mark.asyncio
async def test_get_db_yields_session_and_closes():
    """get_db가 AsyncSession을 yield하고, 컨텍스트 종료 시 세션이 닫히는지 테스트."""
    mock_session = AsyncMock(spec=AsyncSession)

    # AsyncSessionLocal 팩토리 모킹 경로 수정 (db_session 모듈 내의 경로로)
    with patch(
        "app.src.core.dependencies.db_session.AsyncSessionLocal"
    ) as mock_session_factory:
        # 팩토리 호출 시 반환될 비동기 컨텍스트 매니저 모의 객체 설정
        # 이 객체는 __aenter__와 __aexit__를 가져야 함
        mock_context_manager = AsyncMock()
        mock_context_manager.__aenter__.return_value = mock_session
        # __aexit__는 기본적으로 AsyncMock에 의해 모킹됨

        # 팩토리가 이 컨텍스트 매니저 객체를 반환하도록 설정
        mock_session_factory.return_value = mock_context_manager

        # get_db() 호출 및 테스트
        session_generator = get_db()
        yielded_session = await session_generator.__anext__()

        assert yielded_session is mock_session

        with pytest.raises(StopAsyncIteration):
            await session_generator.__anext__()

        # __aenter__와 __aexit__가 호출되었는지 확인
        mock_context_manager.__aenter__.assert_awaited_once()
        mock_context_manager.__aexit__.assert_awaited_once()
