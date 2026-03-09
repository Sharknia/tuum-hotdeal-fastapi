from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.domain.admin.models import WorkerLog, WorkerStatus


async def get_all_worker_logs(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> list[WorkerLog]:
    result = await db.execute(
        select(WorkerLog).order_by(WorkerLog.run_at.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())


async def get_worker_log_monitor(
    db: AsyncSession,
    window_minutes: int,
) -> dict[str, int | bool | datetime | None]:
    now = datetime.now()
    safe_window = max(1, window_minutes)
    window_start = now - timedelta(minutes=safe_window)
    result = await db.execute(
        select(WorkerLog)
        .where(WorkerLog.run_at >= window_start)
        .order_by(WorkerLog.run_at.desc())
    )
    recent_logs = list(result.scalars().all())

    success_logs = [log for log in recent_logs if log.status == WorkerStatus.SUCCESS]
    success_with_mail_logs = [log for log in success_logs if (log.emails_sent or 0) > 0]

    return {
        "evaluated_at": now,
        "window_minutes": safe_window,
        "total_runs_in_window": len(recent_logs),
        "success_runs_in_window": len(success_logs),
        "success_with_mail_runs_in_window": len(success_with_mail_logs),
        "last_success_at": success_logs[0].run_at if success_logs else None,
        "last_mail_sent_at": (
            success_with_mail_logs[0].run_at if success_with_mail_logs else None
        ),
        "alert_no_recent_success": len(success_logs) == 0,
        "alert_zero_mail_in_window": len(success_logs) > 0
        and len(success_with_mail_logs) == 0,
    }
