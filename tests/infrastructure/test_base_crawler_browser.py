from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler


class MockHttpxCrawler(BaseCrawler):
    """httpx를 사용하는 테스트용 크롤러"""

    requires_browser = False

    @property
    def url(self) -> str:
        return "https://httpx-site.com"

    @property
    def site_name(self) -> SiteName:
        return SiteName.ALGUMON

    def parse(self, html: str) -> list[CrawledKeyword]:
        return []


class MockBrowserCrawler(BaseCrawler):
    """Playwright를 사용하는 테스트용 크롤러"""

    requires_browser = True

    @property
    def url(self) -> str:
        return "https://browser-site.com"

    @property
    def site_name(self) -> SiteName:
        return SiteName.FMKOREA

    def parse(self, html: str) -> list[CrawledKeyword]:
        return []


class TestRequiresBrowserAttribute:
    """requires_browser 속성 테스트"""

    def test_base_crawler_has_requires_browser_attribute(self):
        """BaseCrawler는 requires_browser 클래스 속성을 가져야 함"""
        assert hasattr(BaseCrawler, "requires_browser")

    def test_requires_browser_default_is_false(self):
        """requires_browser 기본값은 False여야 함"""
        mock_client = MagicMock()
        crawler = MockHttpxCrawler(keyword="test", client=mock_client)
        assert crawler.requires_browser is False

    def test_requires_browser_can_be_overridden_to_true(self):
        """requires_browser를 True로 오버라이드할 수 있어야 함"""
        mock_client = MagicMock()
        crawler = MockBrowserCrawler(keyword="test", client=mock_client)
        assert crawler.requires_browser is True


class TestFetchMethodBranching:
    """fetch() 메서드 분기 테스트"""

    @pytest.mark.asyncio
    async def test_httpx_crawler_uses_httpx_fetch(self):
        """requires_browser=False면 httpx로 요청해야 함"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html>httpx content</html>"
        mock_client.get = AsyncMock(return_value=mock_response)

        crawler = MockHttpxCrawler(keyword="test", client=mock_client)
        result = await crawler.fetch()

        mock_client.get.assert_called_once()
        assert result == "<html>httpx content</html>"

    @pytest.mark.asyncio
    async def test_browser_crawler_uses_browser_fetch(self):
        """requires_browser=True면 BrowserFetcher로 요청해야 함"""
        mock_client = MagicMock()

        with patch(
            "app.src.Infrastructure.crawling.base_crawler.BrowserFetcher"
        ) as MockBrowserFetcher:
            mock_fetcher = AsyncMock()
            mock_fetcher.fetch = AsyncMock(return_value="<html>browser content</html>")
            mock_fetcher.__aenter__ = AsyncMock(return_value=mock_fetcher)
            mock_fetcher.__aexit__ = AsyncMock(return_value=None)
            MockBrowserFetcher.return_value = mock_fetcher

            crawler = MockBrowserCrawler(keyword="test", client=mock_client)
            result = await crawler.fetch()

            MockBrowserFetcher.assert_called_once()
            mock_fetcher.fetch.assert_called_once()
            assert result == "<html>browser content</html>"

    @pytest.mark.asyncio
    async def test_browser_fetch_returns_none_on_failure(self):
        """BrowserFetcher 실패 시 None 반환"""
        mock_client = MagicMock()

        with patch(
            "app.src.Infrastructure.crawling.base_crawler.BrowserFetcher"
        ) as MockBrowserFetcher:
            mock_fetcher = AsyncMock()
            mock_fetcher.fetch = AsyncMock(return_value=None)
            mock_fetcher.__aenter__ = AsyncMock(return_value=mock_fetcher)
            mock_fetcher.__aexit__ = AsyncMock(return_value=None)
            MockBrowserFetcher.return_value = mock_fetcher

            crawler = MockBrowserCrawler(keyword="test", client=mock_client)
            result = await crawler.fetch()

            assert result is None

    @pytest.mark.asyncio
    async def test_httpx_crawler_retries_with_proxy_on_429(self):
        """429 응답 시 Retry-After를 반영해 대기 후 프록시 재시도해야 함"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_response.headers = {"Retry-After": "7"}
        mock_client.get = AsyncMock(return_value=mock_response)

        crawler = MockHttpxCrawler(keyword="test", client=mock_client)

        with (
            patch.object(
                crawler,
                "_fetch_with_proxy",
                new=AsyncMock(return_value="<html>proxy content</html>"),
            ) as mock_proxy_fetch,
            patch(
                "app.src.Infrastructure.crawling.base_crawler.asyncio.sleep",
                new=AsyncMock(),
            ) as mock_sleep,
        ):
            result = await crawler.fetch()

        mock_proxy_fetch.assert_awaited_once_with("https://httpx-site.com", 10)
        mock_sleep.assert_awaited_once_with(7.0)
        assert result == "<html>proxy content</html>"

    @pytest.mark.asyncio
    async def test_httpx_crawler_caps_retry_after_seconds(self):
        """Retry-After 숫자값이 과도하면 최대 백오프로 제한해야 함"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        mock_response.headers = {"Retry-After": "600"}
        mock_client.get = AsyncMock(return_value=mock_response)

        crawler = MockHttpxCrawler(keyword="test", client=mock_client)

        with (
            patch.object(
                crawler,
                "_fetch_with_proxy",
                new=AsyncMock(return_value="<html>proxy content</html>"),
            ) as mock_proxy_fetch,
            patch(
                "app.src.Infrastructure.crawling.base_crawler.asyncio.sleep",
                new=AsyncMock(),
            ) as mock_sleep,
        ):
            result = await crawler.fetch()

        mock_proxy_fetch.assert_awaited_once_with("https://httpx-site.com", 10)
        mock_sleep.assert_awaited_once_with(60.0)
        assert result == "<html>proxy content</html>"

    @pytest.mark.asyncio
    async def test_httpx_crawler_parses_retry_after_http_date(self):
        """Retry-After HTTP-date 포맷도 파싱하여 최대 백오프로 제한해야 함"""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = "Too Many Requests"
        future_at = datetime.now(UTC) + timedelta(minutes=10)
        mock_response.headers = {"Retry-After": format_datetime(future_at)}
        mock_client.get = AsyncMock(return_value=mock_response)

        crawler = MockHttpxCrawler(keyword="test", client=mock_client)

        with (
            patch.object(
                crawler,
                "_fetch_with_proxy",
                new=AsyncMock(return_value="<html>proxy content</html>"),
            ) as mock_proxy_fetch,
            patch(
                "app.src.Infrastructure.crawling.base_crawler.asyncio.sleep",
                new=AsyncMock(),
            ) as mock_sleep,
        ):
            result = await crawler.fetch()

        mock_proxy_fetch.assert_awaited_once_with("https://httpx-site.com", 10)
        mock_sleep.assert_awaited_once_with(60.0)
        assert result == "<html>proxy content</html>"
