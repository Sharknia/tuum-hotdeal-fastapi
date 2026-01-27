from uuid import uuid4

import pytest

from app.src.core.dependencies.auth import authenticate_admin_user
from app.src.domain.admin.models import WorkerLog, WorkerStatus
from app.src.domain.hotdeal.models import Keyword
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.schemas import AuthenticatedUser


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
