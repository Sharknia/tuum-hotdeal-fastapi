from urllib.parse import urlencode

from bs4 import BeautifulSoup

from app.src.core.logger import logger
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler


class AlgumonCrawler(BaseCrawler):
    @property
    def url(self) -> str:
        query = urlencode({"keyword": self.keyword})
        return f"https://www.algumon.com/n/deal?{query}"

    @property
    def site_name(self) -> SiteName:
        return SiteName.ALGUMON

    def parse(self, html: str) -> list[CrawledKeyword]:
        soup = BeautifulSoup(html, "html.parser")
        deal_cards = soup.find_all("div", id=lambda value: value and value.startswith("deal-"))
        if not deal_cards:
            logger.warning("알구몬 딜 카드를 찾을 수 없습니다.")
            return []

        products = []
        for card in deal_cards:
            post_id = card.get("id", "").removeprefix("deal-").strip()
            title_anchor = card.select_one("h3 a[href]")
            if not post_id or title_anchor is None:
                continue

            title = self._normalize_text(title_anchor)
            if not title:
                continue

            source_meta = self._find_card_block(
                card,
                "div",
                {"flex", "items-center", "gap-1", "mb-1.5"},
            )
            price_meta = self._find_card_block(
                card,
                "div",
                {"flex", "items-center", "gap-1", "text-xs", "mb-1", "mt-1"},
            )
            stats_meta = self._find_card_block(
                card,
                "div",
                {"flex", "gap-2", "text-xs", "mb-0.5"},
            )
            meta_segments = [
                self._normalize_text(source_meta),
                self._normalize_text(price_meta),
                self._normalize_text(stats_meta),
            ]

            products.append(
                CrawledKeyword(
                    id=post_id,
                    title=title,
                    link=f"https://www.algumon.com/n/deal/{post_id}",
                    price=self._normalize_text(card.find("p", class_="deal-price-text")),
                    meta_data=" | ".join(segment for segment in meta_segments if segment) or None,
                    site_name=self.site_name,
                    search_url=self.search_url,
                )
            )
        return products

    @staticmethod
    def _normalize_text(node) -> str | None:
        if node is None:
            return None
        text = " ".join(" ".join(node.stripped_strings).split())
        return text or None

    @staticmethod
    def _find_card_block(card, name: str, required_classes: set[str]):
        for node in card.find_all(name):
            classes = set(node.get("class") or [])
            if required_classes.issubset(classes):
                return node
        return None
