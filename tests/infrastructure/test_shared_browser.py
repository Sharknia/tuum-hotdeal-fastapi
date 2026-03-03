import asyncio
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


@pytest.mark.asyncio
async def test_idempotent_start_stop():
    with patch("app.src.Infrastructure.crawling.shared_browser.async_playwright") as mock_ap:
        mock_playwright_instance = AsyncMock()
        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright_instance)

        mock_browser = AsyncMock()
        mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)

        shared_browser = SharedBrowser.get_instance()
        await shared_browser.start()
        await shared_browser.start()

        await shared_browser.stop()
        await shared_browser.stop()

        mock_ap.return_value.start.assert_called_once()
        mock_playwright_instance.chromium.launch.assert_called_once_with(headless=True)
        mock_browser.close.assert_called_once()
        mock_playwright_instance.stop.assert_called_once()


@pytest.mark.asyncio
async def test_concurrent_start_single_launch():
    with patch("app.src.Infrastructure.crawling.shared_browser.async_playwright") as mock_ap:
        mock_playwright_instance = AsyncMock()
        mock_ap.return_value.start = AsyncMock(return_value=mock_playwright_instance)

        mock_browser = AsyncMock()

        async def delayed_launch(**kwargs):
            await asyncio.sleep(0.01)
            return mock_browser

        mock_playwright_instance.chromium.launch = AsyncMock(side_effect=delayed_launch)

        shared_browser = SharedBrowser.get_instance()

        await asyncio.gather(shared_browser.start(), shared_browser.start(), shared_browser.start())

        mock_ap.return_value.start.assert_called_once()
        assert mock_playwright_instance.chromium.launch.call_count == 1
        assert shared_browser.browser == mock_browser


@pytest.mark.asyncio
async def test_stop_timeout_resets_state():
    with patch("app.src.Infrastructure.crawling.shared_browser.async_playwright") as mock_ap:
        first_playwright = AsyncMock()
        second_playwright = AsyncMock()

        first_browser = AsyncMock()
        second_browser = AsyncMock()

        async def slow_close():
            await asyncio.sleep(0.05)

        first_browser.close = AsyncMock(side_effect=slow_close)
        first_playwright.chromium.launch = AsyncMock(return_value=first_browser)
        second_playwright.chromium.launch = AsyncMock(return_value=second_browser)

        mock_ap.return_value.start = AsyncMock(side_effect=[first_playwright, second_playwright])

        shared_browser = SharedBrowser()
        shared_browser._shutdown_timeout_seconds = 0.01

        await shared_browser.start()
        await shared_browser.stop()

        assert shared_browser.browser is None
        assert shared_browser._playwright is None
        first_playwright.stop.assert_called_once()

        await shared_browser.start()
        assert shared_browser.browser == second_browser


@pytest.mark.asyncio
async def test_stop_exception_does_not_break_next_start():
    with patch("app.src.Infrastructure.crawling.shared_browser.async_playwright") as mock_ap:
        first_playwright = AsyncMock()
        second_playwright = AsyncMock()

        first_browser = AsyncMock()
        second_browser = AsyncMock()

        first_browser.close = AsyncMock(side_effect=RuntimeError("close failed"))
        first_playwright.chromium.launch = AsyncMock(return_value=first_browser)
        second_playwright.chromium.launch = AsyncMock(return_value=second_browser)

        mock_ap.return_value.start = AsyncMock(side_effect=[first_playwright, second_playwright])

        shared_browser = SharedBrowser()

        await shared_browser.start()
        await shared_browser.stop()

        assert shared_browser.browser is None
        assert shared_browser._playwright is None
        first_playwright.stop.assert_called_once()

        await shared_browser.start()
        assert shared_browser.browser == second_browser
