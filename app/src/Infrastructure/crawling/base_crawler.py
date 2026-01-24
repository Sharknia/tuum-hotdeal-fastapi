from abc import ABC, abstractmethod

import httpx

from app.src.core.logger import logger
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.browser_fetcher import BrowserFetcher
from app.src.Infrastructure.crawling.proxy_manager import ProxyManager


class BaseCrawler(ABC):
    requires_browser: bool = False

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
        logger.info(f"[{self.keyword}] 요청: {url}")
        try:
            response = await self.client.get(url, timeout=timeout)

            if response.status_code in [403, 430]:
                if response.status_code == 430:
                    logger.error(f"{response.status_code}: {response.text}")
                logger.warning(
                    f"{response.status_code}: 접근이 차단되었습니다. 프록시로 재시도합니다."
                )
                return await self._fetch_with_proxy(url, timeout)

            response.raise_for_status()
            logger.info(f"[{self.keyword}] 요청 성공: {url}")
            return response.text

        except httpx.RequestError as e:
            logger.error(f"[{self.keyword}] 요청 실패: {e}")
            return None

    async def _fetch_with_browser(self, url: str, wait_seconds: int = 3) -> str | None:
        logger.info(f"[{self.keyword}] 브라우저 요청: {url}")
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

                    if response.status_code in [403, 430]:
                        logger.warning(
                            f"프록시 {proxy_url}에서 {response.status_code} 발생. 실패 목록에 추가합니다."
                        )
                        self.proxy_manager.remove_proxy(proxy_url)
                        continue
                    elif response.status_code == 200:
                        logger.info(f"프록시 {proxy_url}로 요청 성공")
                        return response.text

            except httpx.RequestError as e:
                logger.warning(
                    f"프록시 {proxy_url}로 요청 실패: {e}. 실패 목록에 추가합니다."
                )
                self.proxy_manager.remove_proxy(proxy_url)
                continue

        logger.error(f"[{self.keyword}] 모든 프록시를 사용했지만 요청에 실패했습니다.")
        return None

    async def fetchparse(self) -> list[CrawledKeyword]:
        html = await self.fetch()
        if html:
            self.results = self.parse(html)
        else:
            logger.error(f"[{self.keyword}] 크롤링 실패: {self.url}")
        return self.results
