from unittest.mock import AsyncMock, patch

import pytest

from app.src.Infrastructure.crawling.shared_browser import SharedBrowser


@pytest.mark.asyncio
async def test_shared_browser_singleton():
    instance1 = SharedBrowser.get_instance()
    instance2 = SharedBrowser.get_instance()
    assert instance1 is instance2

@pytest.mark.asyncio
async def test_start_launches_browser():
    with patch("app.src.Infrastructure.crawling.shared_browser.async_playwright") as mock_ap:
        mock_playwright_instance = AsyncMock()
        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright_instance)

        mock_browser = AsyncMock()
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)

        shared_browser = SharedBrowser.get_instance()
        await shared_browser.start()

        mock_ap.return_value.start.assert_called_once()
        mock_playwright_instance.chromium.launch.assert_called_once_with(headless=True)
        assert shared_browser.browser == mock_browser

@pytest.mark.asyncio
async def test_stop_closes_browser():
    with patch("app.src.Infrastructure.crawling.shared_browser.async_playwright") as mock_ap:
        mock_playwright_instance = AsyncMock()
        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright_instance)

        mock_browser = AsyncMock()
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)

        shared_browser = SharedBrowser.get_instance()
        await shared_browser.start()
        await shared_browser.stop()

        mock_browser.close.assert_called_once()
        mock_playwright_instance.stop.assert_called_once()
        assert shared_browser.browser is None
        assert shared_browser._playwright is None
