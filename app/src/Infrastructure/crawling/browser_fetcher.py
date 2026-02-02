import re
from typing import ClassVar, Self

from app.src.core.logger import logger
from app.src.Infrastructure.crawling.shared_browser import SharedBrowser

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

    async def _ensure_browser(self):
        return await SharedBrowser.get_instance().get_browser()

    async def fetch(self, url: str, wait_seconds: int = 3) -> str | None:
        try:
            browser = await self._ensure_browser()
            if browser is None:
                logger.error("[BrowserFetcher] Browser instance is None")
                return None

            context = await browser.new_context(
                user_agent=self.user_agent,
                locale=self.locale,
                viewport={"width": 1920, "height": 1080},
            )

            try:
                await context.route(
                    BLOCKED_RESOURCE_PATTERNS,
                    lambda route: route.abort(),
                )

                page = await context.new_page()
                logger.debug(f"[BrowserFetcher] 요청: {url}")

                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(wait_seconds * 1000)

                html = await page.content()

                for attempt in range(self.max_challenge_retries):
                    if not self._is_challenge_page(html):
                        break
                    logger.debug(
                        f"[BrowserFetcher] 챌린지 감지, 재시도 {attempt + 1}/{self.max_challenge_retries}"
                    )
                    await page.wait_for_timeout(3000)
                    html = await page.content()

                if self._is_challenge_page(html):
                    logger.warning("[BrowserFetcher] 챌린지 페이지 통과 실패")
                    return None

                logger.debug(f"[BrowserFetcher] 요청 성공: {url} ({len(html)} bytes)")
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
        pass

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
