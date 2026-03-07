import asyncio
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from math import isfinite

import httpx

from app.src.core.config import settings
from app.src.core.logger import logger
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher
from app.src.Infrastructure.crawling.proxy_manager import ProxyManager


class BaseCrawler(ABC):
    requires_browser: bool = False
    blocked_status_codes: set[int] = {403, 429, 430}

    def __init__(
        self,
        keyword: str,
        client: httpx.AsyncClient,
    ):
        self.keyword = keyword
        self.proxy_manager: ProxyManager = ProxyManager()
        self.results = []
        self.client = client

    @property
    @abstractmethod
    def url(self) -> str:
        pass

    @property
    @abstractmethod
    def site_name(self) -> SiteName:
        pass

    @property
    def search_url(self) -> str:
        return self.url

    @abstractmethod
    def parse(self, html: str) -> list[CrawledKeyword]:
        pass

    async def fetch(self, url: str | None = None, timeout: int = 10) -> str | None:
        target_url = url or self.url

        if self.requires_browser:
            return await self._fetch_with_browser(target_url)

        return await self._fetch_with_httpx(target_url, timeout)

    async def _fetch_with_httpx(self, url: str, timeout: int = 10) -> str | None:
        logger.debug(f"[{self.keyword}] 요청: {url}")
        try:
            response = await self.client.get(url, timeout=timeout)

            if response.status_code in self.blocked_status_codes:
                backoff_seconds = self._get_backoff_seconds(response)
                if response.status_code == 430:
                    logger.error(f"{response.status_code}: {response.text}")
                logger.warning(
                    "%s: 접근이 차단되었습니다. %.1f초 대기 후 프록시로 재시도합니다.",
                    response.status_code,
                    backoff_seconds,
                )
                await asyncio.sleep(backoff_seconds)
                return await self._fetch_with_proxy(url, timeout)

            response.raise_for_status()
            logger.debug(f"[{self.keyword}] 요청 성공: {url}")
            return response.text

        except httpx.RequestError as e:
            logger.error(f"[{self.keyword}] 요청 실패: {e}")
            return None

    async def _fetch_with_browser(self, url: str, wait_seconds: int = 3) -> str | None:
        logger.debug(f"[{self.keyword}] 브라우저 요청: {url}")
        async with BrowserFetcher() as fetcher:
            return await fetcher.fetch(url, wait_seconds=wait_seconds)

    async def _fetch_with_proxy(self, url: str, timeout: int = 20) -> str | None:
        for _ in range(15):
            proxy_url = self.proxy_manager.get_next_proxy()
            if not proxy_url:
                logger.error("사용할 수 있는 프록시가 없습니다.")
                return None

            try:
                async with httpx.AsyncClient(proxy=proxy_url) as proxy_client:
                    response = await proxy_client.get(url, timeout=timeout)

                    if response.status_code in self.blocked_status_codes:
                        backoff_seconds = self._get_backoff_seconds(response)
                        logger.warning(
                            "프록시 %s에서 %s 발생. 실패 목록에 추가 후 %.1f초 대기합니다.",
                            proxy_url,
                            response.status_code,
                            backoff_seconds,
                        )
                        self.proxy_manager.remove_proxy(proxy_url)
                        await asyncio.sleep(backoff_seconds)
                        continue
                    elif response.status_code == 200:
                        logger.debug(f"프록시 {proxy_url}로 요청 성공")
                        return response.text

            except httpx.RequestError as e:
                logger.warning(
                    f"프록시 {proxy_url}로 요청 실패: {e}. 실패 목록에 추가합니다."
                )
                self.proxy_manager.remove_proxy(proxy_url)
                continue

        logger.error(f"[{self.keyword}] 모든 프록시를 사용했지만 요청에 실패했습니다.")
        return None

    def _get_backoff_seconds(self, response: httpx.Response) -> float:
        base_backoff = max(0.5, settings.CRAWL_BLOCK_BACKOFF_SECONDS)
        max_backoff = max(base_backoff, settings.CRAWL_BLOCK_BACKOFF_MAX_SECONDS)
        retry_after = response.headers.get("Retry-After")
        if not retry_after:
            return base_backoff

        retry_after_seconds = self._parse_retry_after_seconds(retry_after)
        if retry_after_seconds is None:
            return base_backoff

        return min(max_backoff, max(base_backoff, retry_after_seconds))

    def _parse_retry_after_seconds(self, retry_after: str) -> float | None:
        try:
            retry_after_seconds = float(retry_after)
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(retry_after)
            except (TypeError, ValueError, OverflowError):
                return None

            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=UTC)

            retry_after_seconds = (retry_at - datetime.now(UTC)).total_seconds()

        if not isfinite(retry_after_seconds):
            return None

        return max(0.0, retry_after_seconds)

    async def fetchparse(self) -> list[CrawledKeyword]:
        html = await self.fetch()
        if html:
            self.results = self.parse(html)
        else:
            logger.error(f"[{self.keyword}] 크롤링 실패: {self.url}")
        return self.results
