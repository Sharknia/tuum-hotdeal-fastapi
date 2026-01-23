import re

from bs4 import BeautifulSoup

from app.src.core.logger import logger
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler


class RuliwebCrawler(BaseCrawler):
    @property
    def url(self) -> str:
        return f"https://bbs.ruliweb.com/market/board/1020?search_type=subject&search_key={self.keyword}"

    @property
    def site_name(self) -> SiteName:
        return SiteName.RULIWEB

    def parse(self, html: str) -> list[CrawledKeyword]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", class_="board_list_table")
        if not table:
            logger.warning("루리웹 게시판 테이블을 찾을 수 없습니다.")
            return []

        products = []
        for row in table.find_all("tr", class_="table_body"):
            classes = row.get("class", [])
            if "notice" in classes or "best" in classes:
                continue

            id_td = row.find("td", class_="id")
            subject_td = row.find("td", class_="subject")

            if not id_td or not subject_td:
                continue

            post_id = id_td.get_text(strip=True)
            if not post_id.isdigit():
                continue

            subject_link = subject_td.find("a", class_="subject_link")
            if not subject_link:
                continue

            link = subject_link.get("href", "")
            title_text = subject_link.get_text(strip=True)
            title = re.sub(r"\s*\(\d+\)\s*$", "", title_text).strip()

            price = None
            price_match = re.search(r"[\d,]+원", title)
            if price_match:
                price = price_match.group()

            products.append(
                CrawledKeyword(
                    id=post_id,
                    title=title,
                    link=link,
                    price=price,
                    meta_data="",
                    site_name=self.site_name,
                    search_url=self.search_url,
                )
            )

        return products
