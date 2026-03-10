from urllib.parse import urlencode

from bs4 import BeautifulSoup, Tag

from app.src.core.logger import logger
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler


class AlgumonCrawler(BaseCrawler):
    SEARCH_URL_BASE = "https://www.algumon.com/n/deal"
    DEAL_URL_TEMPLATE = "https://www.algumon.com/n/deal/{post_id}"
    DEAL_CARD_ID_PREFIX = "deal-"
    TITLE_SELECTOR = "h3 a[href]"
    PRICE_CLASS = "deal-price-text"
    SOURCE_META_CLASSES = frozenset({"flex", "items-center", "gap-1", "mb-1.5"})
    PRICE_META_CLASSES = frozenset(
        {"flex", "items-center", "gap-1", "text-xs", "mb-1", "mt-1"}
    )
    STATS_META_CLASSES = frozenset({"flex", "gap-2", "text-xs", "mb-0.5"})

    @property
    def url(self) -> str:
        query = urlencode({"keyword": self.keyword})
        return f"{self.SEARCH_URL_BASE}?{query}"

    @property
    def site_name(self) -> SiteName:
        return SiteName.ALGUMON

    def parse(self, html: str) -> list[CrawledKeyword]:
        soup = BeautifulSoup(html, "html.parser")
        deal_cards = soup.find_all(
            "div",
            id=lambda value: value and value.startswith(self.DEAL_CARD_ID_PREFIX),
        )
        if not deal_cards:
            logger.warning("알구몬 딜 카드를 찾을 수 없습니다.")
            return []

        products: list[CrawledKeyword] = []
        for card in deal_cards:
            post_id = card.get("id", "").removeprefix(self.DEAL_CARD_ID_PREFIX).strip()
            title_anchor = card.select_one(self.TITLE_SELECTOR)
            if not post_id or title_anchor is None:
                continue

            title = self._normalize_text(title_anchor)
            if not title:
                continue

            meta_segments = [
                self._normalize_text(
                    self._find_card_block(card, "div", self.SOURCE_META_CLASSES)
                ),
                self._normalize_text(
                    self._find_card_block(card, "div", self.PRICE_META_CLASSES)
                ),
                self._normalize_text(
                    self._find_card_block(card, "div", self.STATS_META_CLASSES)
                ),
            ]

            products.append(
                CrawledKeyword(
                    id=post_id,
                    title=title,
                    link=self.DEAL_URL_TEMPLATE.format(post_id=post_id),
                    price=self._normalize_text(card.find("p", class_=self.PRICE_CLASS)),
                    meta_data=" | ".join(segment for segment in meta_segments if segment)
                    or None,
                    site_name=self.site_name,
                    search_url=self.search_url,
                )
            )
        return products

    @staticmethod
    def _normalize_text(node: Tag | None) -> str | None:
        if node is None:
            return None
        text = " ".join(" ".join(node.stripped_strings).split())
        return text or None

    @staticmethod
    def _find_card_block(
        card: Tag,
        name: str,
        required_classes: frozenset[str],
    ) -> Tag | None:
        for node in card.find_all(name):
            classes = set(node.get("class") or [])
            if required_classes.issubset(classes):
                return node
        return None
