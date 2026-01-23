import re
from contextlib import asynccontextmanager
from typing import ClassVar, Self

from playwright.async_api import async_playwright

from app.src.core.logger import logger

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

CHALLENGE_INDICATORS = ["cf-turnstile", "challenge-running", "cf-browser-verification"]

BLOCKED_RESOURCE_PATTERNS = re.compile(
    r"\.(png|jpg|jpeg|gif|webp|svg|woff|woff2|ttf)$|"
    r"(google-analytics|googletagmanager|facebook|doubleclick)"
)


class BrowserFetcher:
    max_challenge_retries: ClassVar[int] = 3

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        headless: bool = True,
        locale: str = "ko-KR",
    ):
        self.user_agent = user_agent
        self.headless = headless
        self.locale = locale
        self._playwright = None
        self._browser = None

    async def _ensure_browser(self):
        if self._browser is None:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
        return self._browser

    async def fetch(self, url: str, wait_seconds: int = 3) -> str | None:
        try:
            browser = await self._ensure_browser()
            context = await browser.new_context(
                user_agent=self.user_agent,
                locale=self.locale,
                viewport={"width": 1920, "height": 1080},
            )

            await context.route(
                BLOCKED_RESOURCE_PATTERNS,
                lambda route: route.abort(),
            )

            try:
                page = await context.new_page()
                logger.info(f"[BrowserFetcher] 요청: {url}")

                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(wait_seconds * 1000)

                html = await page.content()

                for attempt in range(self.max_challenge_retries):
                    if not self._is_challenge_page(html):
                        break
                    logger.info(
                        f"[BrowserFetcher] 챌린지 감지, 재시도 {attempt + 1}/{self.max_challenge_retries}"
                    )
                    await page.wait_for_timeout(3000)
                    html = await page.content()

                if self._is_challenge_page(html):
                    logger.warning("[BrowserFetcher] 챌린지 페이지 통과 실패")
                    return None

                logger.info(f"[BrowserFetcher] 요청 성공: {url} ({len(html)} bytes)")
                return html

            finally:
                await context.close()

        except Exception as e:
            logger.error(f"[BrowserFetcher] 요청 실패: {e}")
            return None

    def _is_challenge_page(self, html: str) -> bool:
        html_lower = html.lower()
        return any(indicator in html_lower for indicator in CHALLENGE_INDICATORS)

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
