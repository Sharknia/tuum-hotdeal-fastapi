import asyncio
import os
import signal
from typing import ClassVar, Optional

from playwright.async_api import Browser, Playwright, async_playwright

from app.src.core.logger import logger


class SharedBrowser:
    _instance: ClassVar[Optional["SharedBrowser"]] = None
    _current_test: ClassVar[str | None] = None
    _shutdown_timeout_seconds: ClassVar[float] = 15.0
    _force_kill_wait_seconds: ClassVar[float] = 3.0

    def __init__(self) -> None:
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._lifecycle_lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "SharedBrowser":
        test_env = os.environ.get("PYTEST_CURRENT_TEST")
        if cls._instance is None or (test_env and cls._current_test != test_env):
            cls._instance = cls()
            cls._current_test = test_env
        return cls._instance

    @property
    def browser(self) -> Browser | None:
        return self._browser

    async def start(self) -> None:
        async with self._lifecycle_lock:
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
            except asyncio.CancelledError:
                logger.warning("[SharedBrowser] Start cancelled. Tearing down browser resources.")
                await self._teardown_unlocked()
                raise
            except Exception as e:
                logger.error(f"[SharedBrowser] Failed to start browser: {e}")
                await self._teardown_unlocked()
                raise

    async def stop(self) -> None:
        async with self._lifecycle_lock:
            if self._browser is None and self._playwright is None:
                logger.debug("[SharedBrowser] Browser is already stopped.")
                return
            await self._teardown_unlocked()

    async def _teardown_unlocked(self) -> None:
        browser_pid = self._extract_browser_pid()

        if self._browser:
            logger.info("[SharedBrowser] Closing Browser...")
            try:
                await asyncio.wait_for(
                    self._browser.close(), timeout=self._shutdown_timeout_seconds
                )
            except asyncio.CancelledError:
                logger.warning("[SharedBrowser] Browser close cancelled.")
                await self._force_terminate_browser_process(browser_pid)
                raise
            except TimeoutError:
                logger.error("[SharedBrowser] Timed out while closing browser.")
                await self._force_terminate_browser_process(browser_pid)
            except Exception as e:
                logger.error(f"[SharedBrowser] Error closing browser: {e}")
                await self._force_terminate_browser_process(browser_pid)
            finally:
                self._browser = None

        if self._playwright:
            logger.info("[SharedBrowser] Stopping Playwright...")
            try:
                await asyncio.wait_for(
                    self._playwright.stop(), timeout=self._shutdown_timeout_seconds
                )
            except asyncio.CancelledError:
                logger.warning("[SharedBrowser] Playwright stop cancelled.")
                await self._force_terminate_browser_process(browser_pid)
                raise
            except TimeoutError:
                logger.error("[SharedBrowser] Timed out while stopping playwright.")
                await self._force_terminate_browser_process(browser_pid)
            except Exception as e:
                logger.error(f"[SharedBrowser] Error stopping playwright: {e}")
                await self._force_terminate_browser_process(browser_pid)
            finally:
                self._playwright = None

    def _extract_browser_pid(self) -> int | None:
        if self._browser is None:
            return None

        impl_obj = getattr(self._browser, "_impl_obj", None)
        connection = getattr(impl_obj, "_connection", None)
        transport = getattr(connection, "_transport", None)
        process = getattr(transport, "_proc", None)
        pid = getattr(process, "pid", None)

        if isinstance(pid, int) and pid > 0:
            return pid
        return None

    def _try_reap_process(self, pid: int) -> bool:
        try:
            waited_pid, _ = os.waitpid(pid, os.WNOHANG)
        except ChildProcessError:
            return True
        except Exception as e:
            logger.error(f"[SharedBrowser] waitpid failed for pid={pid}: {e}")
            return False

        return waited_pid == pid

    async def _force_terminate_browser_process(self, pid: int | None) -> None:
        if pid is None:
            return

        if self._try_reap_process(pid):
            return

        for sig in (signal.SIGTERM, signal.SIGKILL):
            try:
                os.kill(pid, sig)
            except ProcessLookupError:
                return
            except Exception as e:
                logger.error(
                    f"[SharedBrowser] Failed to send {sig.name} to pid={pid}: {e}"
                )
                return

            try:
                await asyncio.wait_for(
                    self._wait_until_reaped(pid), timeout=self._force_kill_wait_seconds
                )
                return
            except TimeoutError:
                logger.error(
                    f"[SharedBrowser] Timed out waiting process reap pid={pid} after {sig.name}"
                )
                continue

    async def _wait_until_reaped(self, pid: int) -> None:
        while True:
            if self._try_reap_process(pid):
                return
            await asyncio.sleep(0.1)

    async def get_browser(self) -> Browser | None:
        if self._browser is None:
            await self.start()
        return self._browser
