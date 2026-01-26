import os
from typing import ClassVar, Optional
from playwright.async_api import async_playwright, Playwright, Browser
from app.src.core.logger import logger


class SharedBrowser:
    _instance: ClassVar[Optional["SharedBrowser"]] = None
    _current_test: ClassVar[Optional[str]] = None

    def __init__(self) -> None:
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None

    @classmethod
    def get_instance(cls) -> "SharedBrowser":
        test_env = os.environ.get("PYTEST_CURRENT_TEST")
        if cls._instance is None or (test_env and cls._current_test != test_env):
            cls._instance = cls()
            cls._current_test = test_env
        return cls._instance

    @property
    def browser(self) -> Optional[Browser]:
        return self._browser

    async def start(self) -> None:
        if self._browser is not None:
            logger.debug("[SharedBrowser] Browser is already running.")
            return

        logger.info("[SharedBrowser] Starting Playwright and Browser...")
        try:
            self._playwright = await async_playwright().start()
            
            launch_kwargs = {"headless": True}
            if not os.environ.get("PYTEST_CURRENT_TEST"):
                launch_kwargs["args"] = ["--disable-blink-features=AutomationControlled"]
                
            self._browser = await self._playwright.chromium.launch(**launch_kwargs)
            logger.info("[SharedBrowser] Browser started successfully.")
        except Exception as e:
            logger.error(f"[SharedBrowser] Failed to start browser: {e}")
            await self.stop()
            raise

    async def stop(self) -> None:
        if self._browser:
            logger.info("[SharedBrowser] Closing Browser...")
            try:
                await self._browser.close()
            except Exception as e:
                logger.error(f"[SharedBrowser] Error closing browser: {e}")
            finally:
                self._browser = None

        if self._playwright:
            logger.info("[SharedBrowser] Stopping Playwright...")
            try:
                await self._playwright.stop()
            except Exception as e:
                logger.error(f"[SharedBrowser] Error stopping playwright: {e}")
            finally:
                self._playwright = None

    async def get_browser(self) -> Optional[Browser]:
        if self._browser is None:
            await self.start()
        return self._browser
