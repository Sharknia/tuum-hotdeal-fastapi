from unittest.mock import MagicMock

from app.src.domain.hotdeal.enums import SiteName
from app.src.Infrastructure.crawling.crawlers import (
    CRAWLER_REGISTRY,
    get_active_sites,
    get_crawler,
)
from app.src.Infrastructure.crawling.crawlers.algumon import AlgumonCrawler


class TestCrawlerRegistry:
    def test_algumon_registered_in_registry(self):
        """ALGUMON이 레지스트리에 등록되어 있어야 함"""
        assert SiteName.ALGUMON in CRAWLER_REGISTRY
        assert CRAWLER_REGISTRY[SiteName.ALGUMON] is AlgumonCrawler

    def test_get_crawler_returns_algumon_crawler(self):
        """get_crawler로 AlgumonCrawler 인스턴스를 생성할 수 있어야 함"""
        mock_client = MagicMock()
        crawler = get_crawler(SiteName.ALGUMON, "테스트키워드", mock_client)

        assert isinstance(crawler, AlgumonCrawler)
        assert crawler.keyword == "테스트키워드"
        assert crawler.client is mock_client

    def test_all_registered_sites_are_valid_site_names(self):
        """레지스트리에 등록된 모든 사이트는 유효한 SiteName이어야 함"""
        for site in CRAWLER_REGISTRY:
            assert isinstance(site, SiteName), f"{site} is not a valid SiteName"

    def test_get_active_sites_returns_registered_sites(self):
        """get_active_sites는 등록된 모든 사이트를 반환해야 함"""
        active_sites = get_active_sites()

        assert isinstance(active_sites, list)
        assert SiteName.ALGUMON in active_sites
        assert len(active_sites) == len(CRAWLER_REGISTRY)
