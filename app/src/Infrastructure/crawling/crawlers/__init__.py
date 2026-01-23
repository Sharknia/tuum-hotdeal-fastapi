import httpx

from app.src.domain.hotdeal.enums import SiteName
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler
from app.src.Infrastructure.crawling.crawlers.algumon import AlgumonCrawler

CRAWLER_REGISTRY: dict[SiteName, type[BaseCrawler]] = {
    SiteName.ALGUMON: AlgumonCrawler,
}


def get_crawler(site: SiteName, keyword: str, client: httpx.AsyncClient) -> BaseCrawler:
    if site not in CRAWLER_REGISTRY:
        raise ValueError(f"Unsupported site: {site}")
    return CRAWLER_REGISTRY[site](keyword=keyword, client=client)


def get_active_sites() -> list[SiteName]:
    return list(CRAWLER_REGISTRY.keys())
