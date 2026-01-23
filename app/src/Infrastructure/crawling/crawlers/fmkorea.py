import re

from bs4 import BeautifulSoup

from app.src.core.logger import logger
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.base_crawler import BaseCrawler


class FmkoreaCrawler(BaseCrawler):
    requires_browser = True

    @property
    def url(self) -> str:
        return "https://www.fmkorea.com/hotdeal"

    @property
    def site_name(self) -> SiteName:
        return SiteName.FMKOREA

    def parse(self, html: str) -> list[CrawledKeyword]:
        soup = BeautifulSoup(html, "html.parser")
        items = soup.select(".fm_best_widget .li")
        if not items:
            logger.warning("FM코리아 핫딜 위젯을 찾을 수 없습니다.")
            return []

        products = []
        for row in items:
            # 종료된 핫딜 제외 (hotdeal_var8Y 클래스가 있으면 종료된 딜)
            if row.select_one(".hotdeal_var8Y"):
                continue

            title_tag = row.select_one(".title a")
            if not title_tag:
                continue

            # href에서 게시물 ID 추출 (예: "/7953041" -> "7953041")
            href = title_tag.get("href", "")
            post_id = href.lstrip("/")
            if not post_id.isdigit():
                continue

            # 제목 추출 (get_text 사용, 댓글 수 [N]은 정규식으로 제거)
            title = title_tag.get_text(strip=True)
            title = re.sub(r"\[\d+\]$", "", title).strip()

            # 키워드 필터링 (대소문자 무시)
            if self.keyword.lower() not in title.lower():
                continue

            # 가격 추출 (hotdeal_info에서)
            price = self._extract_price(row)

            # 메타데이터 (쇼핑몰, 배송 정보)
            meta_data = self._extract_meta_data(row)

            products.append(
                CrawledKeyword(
                    id=post_id,
                    title=title,
                    link=f"https://www.fmkorea.com/{post_id}",
                    price=price,
                    meta_data=meta_data,
                    site_name=self.site_name,
                    search_url=self.search_url,
                )
            )

        return products

    def _extract_price(self, row: BeautifulSoup) -> str | None:
        """hotdeal_info에서 가격 정보를 추출합니다."""
        hotdeal_info = row.select_one(".hotdeal_info")
        if not hotdeal_info:
            return None

        for span in hotdeal_info.find_all("span"):
            if "가격" in span.get_text():
                price_link = span.find("a")
                if price_link:
                    return price_link.get_text(strip=True)
        return None

    def _extract_meta_data(self, row: BeautifulSoup) -> str:
        """hotdeal_info에서 쇼핑몰, 배송 정보를 추출합니다."""
        hotdeal_info = row.select_one(".hotdeal_info")
        if not hotdeal_info:
            return ""

        meta_parts = []
        for span in hotdeal_info.find_all("span"):
            text = span.get_text()
            if "쇼핑몰" in text:
                shop_link = span.find("a")
                if shop_link:
                    meta_parts.append(f"쇼핑몰: {shop_link.get_text(strip=True)}")
            elif "배송" in text:
                delivery_link = span.find("a")
                if delivery_link:
                    meta_parts.append(f"배송: {delivery_link.get_text(strip=True)}")

        return " | ".join(meta_parts)
