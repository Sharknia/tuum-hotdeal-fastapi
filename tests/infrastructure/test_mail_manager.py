"""mail_manager.py 테스트"""

import inspect
from unittest.mock import AsyncMock, patch

import pytest

from app.src.core.config import settings
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.models import Keyword
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.mail.mail_manager import (
    make_hotdeal_email_content,
    send_email,
)


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


# --- Phase 4: 멀티사이트 지원 테스트 ---


class TestMakeHotdealEmailContent:
    """make_hotdeal_email_content 함수 테스트"""

    @pytest.mark.asyncio
    async def test_uses_search_url_from_crawled_keyword(self):
        """CrawledKeyword.search_url이 HTML에 포함되어야 함 (하드코딩 URL 제거)"""
        keyword = Keyword(title="테스트키워드")
        custom_search_url = "https://custom-search-url.com/search/테스트"
        updates = [
            CrawledKeyword(
                id="1",
                title="상품1",
                link="http://link1",
                price="1000원",
                site_name=SiteName.ALGUMON,
                search_url=custom_search_url,
            )
        ]

        result = await make_hotdeal_email_content(keyword, updates)

        # CrawledKeyword의 search_url이 사용되어야 함
        assert custom_search_url in result
        # 하드코딩된 알구몬 URL 패턴이 없어야 함
        assert "algumon.com/search/" not in result

    @pytest.mark.asyncio
    async def test_groups_products_by_site_with_site_header(self):
        """사이트별로 상품이 그룹화되고 사이트 헤더가 표시되어야 함"""
        keyword = Keyword(title="테스트키워드")
        updates = [
            CrawledKeyword(
                id="1",
                title="상품1",
                link="http://link1",
                price="1000원",
                site_name=SiteName.ALGUMON,
                search_url="https://algumon.com/search/test",
            ),
            CrawledKeyword(
                id="2",
                title="상품2",
                link="http://link2",
                price="2000원",
                site_name=SiteName.ALGUMON,
                search_url="https://algumon.com/search/test",
            ),
        ]

        result = await make_hotdeal_email_content(keyword, updates)

        # 사이트명이 포함되어야 함
        assert "ALGUMON" in result
        # 상품 정보가 포함되어야 함
        assert "상품1" in result
        assert "상품2" in result

    @pytest.mark.asyncio
    async def test_returns_empty_string_for_empty_list(self):
        """빈 리스트 입력 시 빈 문자열 반환"""
        keyword = Keyword(title="테스트키워드")
        result = await make_hotdeal_email_content(keyword, [])
        assert result == ""

    @pytest.mark.asyncio
    async def test_includes_product_links_and_prices(self):
        """상품 링크와 가격이 포함되어야 함"""
        keyword = Keyword(title="테스트키워드")
        updates = [
            CrawledKeyword(
                id="1",
                title="테스트 상품",
                link="https://example.com/product/1",
                price="15,000원",
                site_name=SiteName.ALGUMON,
                search_url="https://algumon.com/search/test",
            )
        ]

        result = await make_hotdeal_email_content(keyword, updates)

        assert "https://example.com/product/1" in result
        assert "테스트 상품" in result
        assert "15,000원" in result
