import httpx

from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import SiteInfo
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler
from app.src.Infrastructure.crawling.crawlers.algumon import AlgumonCrawler
from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler
from app.src.Infrastructure.crawling.crawlers.ruliweb import RuliwebCrawler

CRAWLER_REGISTRY: dict[SiteName, type[BaseCrawler]] = {
    SiteName.ALGUMON: AlgumonCrawler,
    SiteName.FMKOREA: FmkoreaCrawler,
    SiteName.RULIWEB: RuliwebCrawler,
}

SITE_METADATA: dict[SiteName, dict[str, str]] = {
    SiteName.ALGUMON: {
        "display_name": "알구몬",
        "search_url_template": "https://www.algumon.com/search/{keyword}",
    },
    SiteName.FMKOREA: {
        "display_name": "FM코리아",
        "search_url_template": "https://www.fmkorea.com/search?keyword={keyword}",
    },
    SiteName.RULIWEB: {
        "display_name": "루리웹",
        "search_url_template": "https://bbs.ruliweb.com/market/board/1020?search_type=subject&search_key={keyword}",
    },
}


def get_crawler(site: SiteName, keyword: str, client: httpx.AsyncClient) -> BaseCrawler:
    if site not in CRAWLER_REGISTRY:
        raise ValueError(f"Unsupported site: {site}")
    return CRAWLER_REGISTRY[site](keyword=keyword, client=client)


def get_active_sites() -> list[SiteName]:
    return list(CRAWLER_REGISTRY.keys())


def get_site_info_list() -> list[SiteInfo]:
    return [
        SiteInfo(
            name=site,
            display_name=SITE_METADATA[site]["display_name"],
            search_url_template=SITE_METADATA[site]["search_url_template"],
        )
        for site in CRAWLER_REGISTRY
    ]
