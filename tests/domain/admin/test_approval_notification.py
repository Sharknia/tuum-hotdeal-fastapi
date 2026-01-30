from unittest.mock import AsyncMock, patch

import pytest

from app.src.core.dependencies.auth import authenticate_admin_user
from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.schemas import AuthenticatedUser


@pytest.fixture
def mock_admin():
    return AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000001",
        email="admin@example.com",
        nickname="admin",
        auth_level=AuthLevel.ADMIN,
    )


@pytest.mark.asyncio
async def test_send_approval_notification_calls_send_email():
    """send_approval_notification() 함수가 send_email을 올바르게 호출하는지 테스트"""
    # Arrange
    from app.src.domain.user.services import send_approval_notification

    with patch(
        "app.src.domain.user.services.send_email", new_callable=AsyncMock
    ) as mock_send_email:
        # Act
        await send_approval_notification(
            email="test@example.com", nickname="testuser"
        )

        # Assert
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert call_args.kwargs["subject"] == "[Tuum] 가입이 승인되었습니다"
        assert call_args.kwargs["to"] == "test@example.com"
        assert "testuser" in call_args.kwargs["body"]
        assert "가입이 승인되었습니다" in call_args.kwargs["body"]


@pytest.mark.asyncio
async def test_approve_user_sends_email_on_first_approval(
    mock_client, mock_admin, add_mock_user
):
    """첫 승인 시(is_active=False) 메일이 발송되는지 테스트"""
    # Arrange
    user = await add_mock_user(email="newuser@example.com", nickname="newuser", is_active=False)
    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin

    with patch(
        "app.src.domain.user.services.send_email", new_callable=AsyncMock
    ) as mock_send_email:
        # Act
        response = mock_client.patch(f"/api/admin/users/{user.id}/approve")

        # Assert
        assert response.status_code == 200
        mock_send_email.assert_called_once()
        call_args = mock_send_email.call_args
        assert call_args.kwargs["to"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_approve_user_does_not_send_email_if_already_active(
    mock_client, mock_admin, add_mock_user
):
    """이미 승인된 사용자(is_active=True)에게는 메일이 발송되지 않는지 테스트"""
    # Arrange
    user = await add_mock_user(email="activeuser@example.com", nickname="activeuser", is_active=True)
    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin

    with patch(
        "app.src.domain.user.services.send_email", new_callable=AsyncMock
    ) as mock_send_email:
        # Act
        response = mock_client.patch(f"/api/admin/users/{user.id}/approve")

        # Assert
        assert response.status_code == 200
        mock_send_email.assert_not_called()


@pytest.mark.asyncio
async def test_approve_user_succeeds_even_if_email_fails(
    mock_client, mock_admin, add_mock_user
):
    """메일 발송 실패 시에도 승인이 성공하는지 테스트"""
    # Arrange
    user = await add_mock_user(email="erroruser@example.com", nickname="erroruser", is_active=False)
    mock_client.app.dependency_overrides[authenticate_admin_user] = lambda: mock_admin

    with patch(
        "app.src.domain.user.services.send_email", new_callable=AsyncMock
    ) as mock_send_email:
        # 메일 발송 실패 시뮬레이션
        mock_send_email.side_effect = Exception("SMTP error")

        # Act
        response = mock_client.patch(f"/api/admin/users/{user.id}/approve")

        # Assert
        # 승인은 성공해야 함
        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True
        # 메일은 호출되었어야 함 (실패하더라도)
        mock_send_email.assert_called_once()
