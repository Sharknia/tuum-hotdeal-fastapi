import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler
from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword

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

class TestBaseCrawlerResourceLeak:
    @pytest.mark.asyncio
    async def test_fetch_uses_context_manager_to_ensure_cleanup(self):
        """BaseCrawler.fetch should use BrowserFetcher as a context manager"""
        mock_client = MagicMock()
        
        with patch("app.src.Infrastructure.crawling.base_crawler.BrowserFetcher") as MockBrowserFetcher:
            mock_fetcher_instance = AsyncMock()
            mock_fetcher_instance.fetch = AsyncMock(return_value="<html></html>")
            
            mock_fetcher_instance.__aenter__ = AsyncMock(return_value=mock_fetcher_instance)
            mock_fetcher_instance.__aexit__ = AsyncMock(return_value=None)
            
            MockBrowserFetcher.return_value = mock_fetcher_instance

            crawler = MockBrowserCrawler(keyword="test", client=mock_client)
            await crawler.fetch()

            MockBrowserFetcher.assert_called_once()
            mock_fetcher_instance.__aenter__.assert_called_once()
            mock_fetcher_instance.__aexit__.assert_called_once()


class TestBrowserFetcherRobustness:
    @pytest.mark.asyncio
    async def test_fetch_cleans_up_context_on_setup_failure(self):
        """BrowserFetcher.fetch should close context even if setup (route) fails"""
        
        with patch.object(BrowserFetcher, "_ensure_browser") as mock_ensure:
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            
            mock_ensure.return_value = mock_browser
            mock_browser.new_context.return_value = mock_context
            
            mock_context.route.side_effect = Exception("Route setup failed")
            
            fetcher = BrowserFetcher()
            result = await fetcher.fetch("https://example.com")

            assert result is None
            mock_context.close.assert_called_once()
