from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.src.domain.user.enums import AuthLevel
from app.src.domain.user.repositories import get_all_admins
from app.src.domain.user.schemas import UserResponse
from app.src.domain.user.services import send_new_user_notifications


@pytest.mark.asyncio
async def test_get_all_admins():
    # Arrange
    mock_db = AsyncMock()
    mock_result = MagicMock()
    admin_emails = ["admin1@example.com", "admin2@example.com"]

    mock_result.scalars.return_value.all.return_value = admin_emails
    mock_db.execute.return_value = mock_result

    # Act
    result = await get_all_admins(mock_db)

    # Assert
    assert result == admin_emails
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_send_new_user_notifications():
    # Arrange
    admin_emails = ["admin1@example.com", "admin2@example.com"]
    user_data = UserResponse(
        id=uuid4(),
        email="newuser@example.com",
        nickname="NewGuy",
        is_active=True,
        auth_level=AuthLevel.USER,
        created_at=datetime.now()
    )

    with patch("app.src.domain.user.services.send_email", new_callable=AsyncMock) as mock_send:
        # Act
        await send_new_user_notifications(admin_emails, user_data)

        # Assert
        assert mock_send.call_count == len(admin_emails)

        for email in admin_emails:
            mock_send.assert_any_call(
                subject=f"[Tuum] 신규 회원 가입: {user_data.nickname}",
                to=email,
                body=f"""새로운 회원이 가입했습니다.
이메일: {user_data.email}
닉네임: {user_data.nickname}
관리자: https://hotdeal.tuum.day/admin"""
            )
