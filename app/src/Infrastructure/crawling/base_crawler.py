from abc import ABC, abstractmethod

import httpx

from app.src.core.logger import logger
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.proxy_manager import ProxyManager


class BaseCrawler(ABC):
    """크롤러의 기본 추상 클래스."""

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
    def url(
        self,
    ) -> str:
        """크롤링 대상 URL (하위 클래스에서 구현 필수)."""
        pass

    @property
    @abstractmethod
    def site_name(self) -> SiteName:
        """크롤러가 담당하는 사이트 (하위 클래스에서 구현 필수)."""
        pass

    @property
    def search_url(self) -> str:
        """검색 결과 페이지 URL (기본값: self.url)."""
        return self.url

    @abstractmethod
    def parse(
        self,
        html: str,
    ) -> list[CrawledKeyword]:
        """파싱 로직 (사이트별 구현 필요)."""
        pass

    async def fetch(
        self,
        url: str = None,
        timeout: int = 10,
    ) -> str | None:
        """HTML 가져오기 (프록시 포함)."""
        target_url = url or self.url
        logger.info(f"[{self.keyword}] 요청: {target_url}")
        try:
            response = await self.client.get(target_url, timeout=timeout)

            if response.status_code in [403, 430]:
                if response.status_code == 430:
                    logger.error(f"{response.status_code}: {response.text}")
                logger.warning(
                    f"{response.status_code}: 접근이 차단되었습니다. 프록시로 재시도합니다."
                )
                return await self._fetch_with_proxy(target_url, timeout)

            response.raise_for_status()
            logger.info(f"[{self.keyword}] 요청 성공: {target_url}")
            return response.text

        except httpx.RequestError as e:
            logger.error(f"[{self.keyword}] 요청 실패: {e}")
            return None

    async def _fetch_with_proxy(
        self,
        url: str,
        timeout: int = 20,
    ) -> str | None:
        """프록시를 사용하여 HTML 가져오기."""
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
                        self.proxy_manager.remove_proxy(proxy_url)  # 실패 목록에 추가
                        continue  # 다음 프록시로 계속
                    elif response.status_code == 200:
                        logger.info(f"프록시 {proxy_url}로 요청 성공")
                        return response.text

            except httpx.RequestError as e:
                logger.warning(
                    f"프록시 {proxy_url}로 요청 실패: {e}. 실패 목록에 추가합니다."
                )
                self.proxy_manager.remove_proxy(proxy_url)  # 실패 목록에 추가
                continue  # 다음 프록시로 계속

        logger.error(f"[{self.keyword}] 모든 프록시를 사용했지만 요청에 실패했습니다.")
        return None

    async def fetchparse(
        self,
    ) -> list[CrawledKeyword]:
        """크롤링 실행 (필요 시 오버라이드)."""
        html = await self.fetch()
        if html:
            self.results = self.parse(html)
        else:
            logger.error(f"[{self.keyword}] 크롤링 실패: {self.url}")
        return self.results
