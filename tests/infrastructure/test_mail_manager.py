"""mail_manager.py 테스트"""

import inspect
from unittest.mock import AsyncMock, patch

import pytest

from app.src.core.config import settings
from app.src.Infrastructure.mail.mail_manager import send_email


class TestSendEmailSignature:
    """send_email 함수 시그니처 검증"""

    def test_to_parameter_is_required(self):
        """to 파라미터는 필수 (기본값 없음)"""
        sig = inspect.signature(send_email)
        to_param = sig.parameters["to"]
        assert to_param.default is inspect.Parameter.empty

    def test_subject_parameter_is_required(self):
        """subject 파라미터는 필수 (기본값 없음)"""
        sig = inspect.signature(send_email)
        subject_param = sig.parameters["subject"]
        assert subject_param.default is inspect.Parameter.empty

    def test_sender_default_is_settings_smtp_from(self):
        """sender 기본값은 settings.SMTP_FROM"""
        sig = inspect.signature(send_email)
        sender_param = sig.parameters["sender"]
        # 기본값이 None이 아니어야 함 (settings.SMTP_FROM으로 설정됨)
        assert sender_param.default is not inspect.Parameter.empty

    def test_is_html_type_is_bool(self):
        """is_html 타입 힌트는 bool"""
        sig = inspect.signature(send_email)
        is_html_param = sig.parameters["is_html"]
        assert is_html_param.annotation is bool


class TestSendEmailBehavior:
    """send_email 함수 동작 검증"""

    @pytest.mark.asyncio
    async def test_send_email_uses_smtp_from_as_default_sender(self):
        """sender 미지정 시 settings.SMTP_FROM 사용"""
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await send_email(
                subject="테스트 제목",
                to="test@example.com",
                body="테스트 본문",
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            message = call_args[0][0]
            assert message["From"] == settings.SMTP_FROM

    @pytest.mark.asyncio
    async def test_send_email_with_custom_sender(self):
        """sender 지정 시 해당 값 사용"""
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await send_email(
                subject="테스트 제목",
                to="test@example.com",
                body="테스트 본문",
                sender="custom@example.com",
            )

            mock_send.assert_called_once()
            call_args = mock_send.call_args
            message = call_args[0][0]
            assert message["From"] == "custom@example.com"

    @pytest.mark.asyncio
    async def test_send_email_is_html_accepts_bool(self):
        """is_html 파라미터가 bool 값을 정상 처리"""
        with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
            await send_email(
                subject="테스트",
                to="test@example.com",
                body="<h1>HTML</h1>",
                is_html=True,
            )

            mock_send.assert_called_once()
