from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.src.core.dependencies.auth import authenticate_admin_user
from app.src.domain.admin.models import WorkerLog, WorkerStatus
from app.src.domain.hotdeal.models import Keyword
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.schemas import AuthenticatedUser


def _assert_utc_datetime_string(value: str) -> None:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timedelta(0)


@pytest.fixture
def mock_admin():
    return AuthenticatedUser(
        user_id=uuid4(),
        email="admin@example.com",
        nickname="admin",
        auth_level=AuthLevel.ADMIN
    )

@pytest.mark.asyncio
async def test_get_keywords_list(mock_client, mock_admin, mock_db_session):
    # Setup
    kw1 = Keyword(title="ps5")
    kw2 = Keyword(title="xbox")
    mock_db_session.add_all([kw1, kw2])
    await mock_db_session.commit()

    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin

    # Act
    response = mock_client.get("/api/admin/keywords")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 2

@pytest.mark.asyncio
async def test_delete_keyword(mock_client, mock_admin, mock_db_session):
    # Setup
    kw = Keyword(title="switch")
    mock_db_session.add(kw)
    await mock_db_session.commit()
    await mock_db_session.refresh(kw)

    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin

    # Act
    response = mock_client.delete(f"/api/admin/keywords/{kw.id}")

    # Assert
    assert response.status_code == 204

@pytest.mark.asyncio
async def test_get_worker_logs(mock_client, mock_admin, mock_db_session):
    # Setup
    log = WorkerLog(status=WorkerStatus.SUCCESS, items_found=5)
    mock_db_session.add(log)
    await mock_db_session.commit()

    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin

    # Act
    response = mock_client.get("/api/admin/logs")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 1
    _assert_utc_datetime_string(data["items"][0]["run_at"])


@pytest.mark.asyncio
async def test_get_worker_logs_monitor_alerts_no_recent_success(
    mock_client, mock_admin, mock_db_session
):
    # Setup
    fail_log = WorkerLog(
        status=WorkerStatus.FAIL,
        items_found=0,
        emails_sent=0,
        run_at=datetime.now(UTC) - timedelta(minutes=5),
    )
    mock_db_session.add(fail_log)
    await mock_db_session.commit()

    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin

    # Act
    response = mock_client.get("/api/admin/logs/monitor?window_minutes=30")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["alert_no_recent_success"] is True
    assert data["alert_zero_mail_in_window"] is False
    assert data["success_runs_in_window"] == 0
    _assert_utc_datetime_string(data["evaluated_at"])


@pytest.mark.asyncio
async def test_get_worker_logs_monitor_alerts_zero_mail_in_window(
    mock_client, mock_admin, mock_db_session
):
    # Setup
    success_log = WorkerLog(
        status=WorkerStatus.SUCCESS,
        items_found=3,
        emails_sent=0,
        run_at=datetime.now(UTC) - timedelta(minutes=3),
    )
    mock_db_session.add(success_log)
    await mock_db_session.commit()

    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin

    # Act
    response = mock_client.get("/api/admin/logs/monitor?window_minutes=30")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["alert_no_recent_success"] is False
    assert data["alert_zero_mail_in_window"] is True
    _assert_utc_datetime_string(data["evaluated_at"])
    _assert_utc_datetime_string(data["last_success_at"])


@pytest.mark.asyncio
async def test_get_worker_logs_monitor_passes_when_mail_sent(
    mock_client, mock_admin, mock_db_session
):
    # Setup
    success_mail_log = WorkerLog(
        status=WorkerStatus.SUCCESS,
        items_found=2,
        emails_sent=1,
        run_at=datetime.now(UTC) - timedelta(minutes=2),
    )
    mock_db_session.add(success_mail_log)
    await mock_db_session.commit()

    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin

    # Act
    response = mock_client.get("/api/admin/logs/monitor?window_minutes=30")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["alert_no_recent_success"] is False
    assert data["alert_zero_mail_in_window"] is False
    _assert_utc_datetime_string(data["evaluated_at"])
    _assert_utc_datetime_string(data["last_success_at"])
    _assert_utc_datetime_string(data["last_mail_sent_at"])
