from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.domain.admin.models import WorkerLog


async def get_all_worker_logs(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[WorkerLog]:
    result = await db.execute(select(WorkerLog).order_by(WorkerLog.run_at.desc()).offset(skip).limit(limit))
    return list(result.scalars().all())
