from datetime import UTC, datetime


def utc_now() -> datetime:
    """UTC aware 현재 시각을 반환합니다."""
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """naive/aware datetime을 UTC aware로 정규화합니다."""
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def ensure_utc_or_none(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return ensure_utc(value)
