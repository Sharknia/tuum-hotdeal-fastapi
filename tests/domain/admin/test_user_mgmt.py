import pytest
from uuid import uuid4
from app.src.domain.user.enums import AuthLevel
from app.src.core.dependencies.auth import authenticate_admin_user
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
async def test_get_users_list(mock_client, mock_admin, add_mock_user):
    # Setup
    await add_mock_user(email="user1@example.com", nickname="user1")
    await add_mock_user(email="user2@example.com", nickname="user2")
    
    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin
    
    # Act
    response = mock_client.get("/api/admin/users")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)
    assert len(data["items"]) >= 2
    assert data["total"] >= 2

@pytest.mark.asyncio
async def test_approve_user(mock_client, mock_admin, add_mock_user):
    # Setup
    user = await add_mock_user(email="inactive@example.com", is_active=False)
    
    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin
    
    # Act
    response = mock_client.patch(f"/api/admin/users/{user.id}/approve")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is True
