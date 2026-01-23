from bs4 import BeautifulSoup

from app.src.core.logger import logger
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler


class AlgumonCrawler(BaseCrawler):
    @property
    def url(self) -> str:
        return f"https://www.algumon.com/search/{self.keyword}"

    @property
    def site_name(self) -> SiteName:
        return SiteName.ALGUMON

    def parse(self, html: str) -> list[CrawledKeyword]:
        soup = BeautifulSoup(html, "html.parser")
        product_list = soup.find("ul", class_="product post-list")
        if not product_list:
            logger.warning("알구몬 상품 리스트를 찾을 수 없습니다.")
            return []

        products = []
        for li in product_list.find_all("li"):
            post_id = li.get("data-post-id")
            action_uri = li.get("data-action-uri")
            product_link = li.find("a", class_="product-link")
            product_price = li.find("small", class_="product-price")
            meta_info = li.find("small", class_="deal-price-meta-info")

            if post_id and action_uri and product_link:
                products.append(
                    CrawledKeyword(
                        id=post_id,
                        title=product_link.text.strip(),
                        link=f"https://www.algumon.com{action_uri.strip()}",
                        price=(product_price.text.strip() if product_price else None),
                        meta_data=(meta_info.text.strip() if meta_info else "")
                        .replace("\n", "")
                        .replace("\r", "")
                        .replace(" ", ""),
                        site_name=self.site_name,
                        search_url=self.search_url,
                    )
                )
        return products
