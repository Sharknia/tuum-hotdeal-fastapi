from collections import deque

import requests
from bs4 import BeautifulSoup

from app.src.core.logger import logger


class ProxyManager:
    """싱글톤 프록시 관리자."""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, proxy_url="https://www.sslproxies.org/"):
        if ProxyManager._initialized:
            return
        self.proxy_url = proxy_url
        self.proxies = deque()
        self._bad_proxies = set()
        ProxyManager._initialized = True

    def fetch_proxies(self):
        """무료 프록시를 수집하여 저장."""
        try:
            response = requests.get(self.proxy_url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "html.parser")
            table = soup.find("table", {"class": "table table-striped table-bordered"})

            if not table:
                logger.warning("프록시 테이블을 찾을 수 없습니다.")
                return []

            rows = table.find("tbody").find_all("tr")
            new_proxies = [
                f"http://{row.find_all('td')[0].text.strip()}:{row.find_all('td')[1].text.strip()}"
                for row in rows
                if row.find_all("td")[6].text.strip().lower() == "yes"
                and row.find_all("td")[4].text.strip().lower() == "anonymous"
            ][:15]
            self.proxies.extend(new_proxies)  # deque에 추가

            if self.proxies:
                logger.info(f"프록시 설정 완료: {list(self.proxies)}")
            else:
                logger.warning("HTTPS 지원 및 익명 프록시를 찾지 못했습니다.")

        except Exception as e:
            logger.error(f"프록시 가져오기 실패: {e}")
        return list(self.proxies)

    def reset_proxies(self):
        """프록시 리스트 및 실패 프록시 리스트 초기화."""
        self.proxies.clear()
        self._bad_proxies.clear()
        logger.info("프록시 리스트 초기화 완료")

    def get_next_proxy(self) -> str | None:
        """다음 사용 가능한 프록시를 반환합니다."""
        if not self.proxies:
            logger.warning("사용 가능한 프록시가 없습니다.")
            return None

        for _ in range(len(self.proxies)):
            proxy = self.proxies.popleft()
            if proxy not in self._bad_proxies:
                self.proxies.append(proxy)
                return proxy
            else:
                logger.debug(f"블랙리스트에 있는 프록시 건너뛰기: {proxy}")
        logger.warning("모든 프록시가 블랙리스트에 있거나 유효하지 않습니다.")
        return None

    def remove_proxy(self, proxy_url: str):
        """특정 프록시를 실패 프록시 리스트에 추가."""
        self._bad_proxies.add(proxy_url)
        logger.info(f"프록시 실패 목록에 추가됨: {proxy_url}")
