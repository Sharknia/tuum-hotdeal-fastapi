from unittest.mock import AsyncMock, patch

import pytest


class TestBrowserFetcherInterface:
    """BrowserFetcher 인터페이스 테스트"""

    def test_browser_fetcher_class_exists(self):
        """BrowserFetcher 클래스가 존재해야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        assert BrowserFetcher is not None

    def test_browser_fetcher_has_fetch_method(self):
        """BrowserFetcher는 fetch 메서드를 가져야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        fetcher = BrowserFetcher()
        assert hasattr(fetcher, "fetch")
        assert callable(fetcher.fetch)

    def test_browser_fetcher_has_close_method(self):
        """BrowserFetcher는 close 메서드를 가져야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        fetcher = BrowserFetcher()
        assert hasattr(fetcher, "close")
        assert callable(fetcher.close)


class TestBrowserFetcherFetch:
    """BrowserFetcher.fetch() 메서드 테스트"""

    @pytest.mark.asyncio
    async def test_fetch_returns_html_string(self):
        """fetch()는 HTML 문자열을 반환해야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        with patch("app.src.Infrastructure.crawling.browser_fetcher.SharedBrowser") as mock_shared:
            mock_browser = AsyncMock()
            mock_shared.get_instance.return_value.get_browser = AsyncMock(return_value=mock_browser)

            mock_page = AsyncMock()
            mock_page.content.return_value = "<html><body>Test</body></html>"
            mock_page.goto = AsyncMock()
            mock_page.wait_for_timeout = AsyncMock()

            mock_context = AsyncMock()
            mock_context.new_page.return_value = mock_page
            mock_context.route = AsyncMock()
            mock_context.close = AsyncMock()

            mock_browser.new_context.return_value = mock_context

            fetcher = BrowserFetcher()
            result = await fetcher.fetch("https://example.com")

            assert isinstance(result, str)
            assert "<html>" in result
            mock_shared.get_instance.assert_called()

    @pytest.mark.asyncio
    async def test_fetch_returns_none_on_error(self):
        """fetch()는 에러 시 None을 반환해야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        with patch("app.src.Infrastructure.crawling.browser_fetcher.SharedBrowser") as mock_shared:
            mock_shared.get_instance.side_effect = Exception("Browser error")

            fetcher = BrowserFetcher()
            result = await fetcher.fetch("https://example.com")

            assert result is None

    @pytest.mark.asyncio
    async def test_fetch_retries_on_challenge_page(self):
        """fetch()는 챌린지 페이지 감지 시 재시도해야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        with patch("app.src.Infrastructure.crawling.browser_fetcher.SharedBrowser") as mock_shared:
            mock_browser = AsyncMock()
            mock_shared.get_instance.return_value.get_browser = AsyncMock(return_value=mock_browser)

            mock_page = AsyncMock()
            mock_page.content.side_effect = [
                "<html>cf-turnstile challenge</html>",
                "<html>cf-turnstile still</html>",
                "<html><body>Real content</body></html>",
            ]
            mock_page.goto = AsyncMock()
            mock_page.wait_for_timeout = AsyncMock()

            mock_context = AsyncMock()
            mock_context.new_page.return_value = mock_page
            mock_context.route = AsyncMock()
            mock_context.close = AsyncMock()

            mock_browser.new_context.return_value = mock_context

            fetcher = BrowserFetcher()
            result = await fetcher.fetch("https://example.com", wait_seconds=1)

            assert result == "<html><body>Real content</body></html>"
            assert mock_page.content.call_count == 3


class TestBrowserFetcherConfig:
    """BrowserFetcher 설정 테스트"""

    def test_default_user_agent(self):
        """기본 User-Agent가 브라우저처럼 보여야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        fetcher = BrowserFetcher()
        assert "Mozilla" in fetcher.user_agent
        assert "Chrome" in fetcher.user_agent

    def test_custom_user_agent(self):
        """커스텀 User-Agent를 설정할 수 있어야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        custom_ua = "CustomBot/1.0"
        fetcher = BrowserFetcher(user_agent=custom_ua)
        assert fetcher.user_agent == custom_ua

    def test_default_headless_mode(self):
        """기본적으로 headless 모드여야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        fetcher = BrowserFetcher()
        assert fetcher.headless is True

    def test_headless_can_be_disabled(self):
        """headless 모드를 비활성화할 수 있어야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        fetcher = BrowserFetcher(headless=False)
        assert fetcher.headless is False


class TestBrowserFetcherContextManager:
    """BrowserFetcher 컨텍스트 매니저 테스트"""

    @pytest.mark.asyncio
    async def test_can_use_as_async_context_manager(self):
        """async with 문으로 사용할 수 있어야 함"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        async with BrowserFetcher() as fetcher:
            assert fetcher is not None

    @pytest.mark.asyncio
    async def test_close_cleans_up_browser(self):
        """close()는 브라우저를 직접 닫지 않아야 함 (SharedBrowser가 관리)"""
        from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher

        with patch("app.src.Infrastructure.crawling.browser_fetcher.SharedBrowser") as mock_shared:
            mock_browser = AsyncMock()
            mock_playwright = AsyncMock()
            mock_instance = mock_shared.get_instance.return_value
            mock_instance.get_browser.return_value = mock_browser
            mock_instance._playwright = mock_playwright

            fetcher = BrowserFetcher()
            await fetcher.close()

            mock_browser.close.assert_not_called()
            mock_instance.stop.assert_not_called()
