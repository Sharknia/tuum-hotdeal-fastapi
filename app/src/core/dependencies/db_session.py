from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

# database 모듈에서 AsyncSessionLocal 임포트
from ..database import AsyncSessionLocal


# FastAPI 의존성 주입용 비동기 함수
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            # async with 블록이 세션 close를 자동으로 처리합니다.
            pass
