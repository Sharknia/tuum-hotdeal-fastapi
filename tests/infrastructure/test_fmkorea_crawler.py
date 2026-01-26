from unittest.mock import MagicMock

import pytest
from bs4 import BeautifulSoup

from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler


@pytest.fixture
def fmkorea_html():
    """FM코리아 검색 결과 샘플 HTML (정상 항목 1개, 종료된 항목 1개)"""
    return """
    <div class="fm_best_widget">
        <ul>
            <li class="li">
                <div class="title">
                    <a href="/12345">정상 핫딜 상품 [10]</a>
                </div>
                <div class="hotdeal_info">
                    <span>가격: <a href="#">10,000원</a></span>
                    <span>쇼핑몰: <a href="#">네이버</a></span>
                    <span>배송: <a href="#">무료</a></span>
                </div>
            </li>
            <li class="li hotdeal_var8Y">
                <div class="title">
                    <a href="/67890">종료된 핫딜 상품 [5]</a>
                </div>
                <div class="hotdeal_info">
                    <span>가격: <a href="#">20,000원</a></span>
                    <span>쇼핑몰: <a href="#">쿠팡</a></span>
                    <span>배송: <a href="#">3,000원</a></span>
                </div>
            </li>
        </ul>
    </div>
    """


class TestFmkoreaCrawler:
    @pytest.fixture
    def crawler(self):
        """FmkoreaCrawler 인스턴스 (Mock Client 사용)"""
        mock_client = MagicMock()
        return FmkoreaCrawler(keyword="테스트", client=mock_client)

    def test_site_name(self, crawler):
        """site_name 속성이 SiteName.FMKOREA를 반환해야 함"""
        assert crawler.site_name == SiteName.FMKOREA

    def test_url(self, crawler):
        """url 속성이 올바른 검색 URL을 반환해야 함 (키워드 인코딩 포함)"""
        assert "search.php" in crawler.url
        assert "search_keyword=%ED%85%8C%EC%8A%A4%ED%8A%B8" in crawler.url
        assert "mid=hotdeal" in crawler.url

    def test_parse_success(self, crawler, fmkorea_html):
        """parse()가 정상 항목만 추출하고 종료된 항목은 무시해야 함"""
        results = crawler.parse(fmkorea_html)

        assert len(results) == 1
        item = results[0]

        assert isinstance(item, CrawledKeyword)
        assert item.id == "12345"
        assert item.title == "정상 핫딜 상품"
        assert item.price == "10,000원"
        assert "쇼핑몰: 네이버" in item.meta_data
        assert "배송: 무료" in item.meta_data
        assert item.site_name == SiteName.FMKOREA

    def test_extract_post_id(self, crawler):
        """_extract_post_id가 다양한 URL 형식에서 ID를 올바르게 추출해야 함"""
        assert crawler._extract_post_id("/12345") == "12345"
        assert crawler._extract_post_id("/index.php?document_srl=12345&mid=hotdeal") == "12345"
        assert crawler._extract_post_id("/abcde") is None
        assert crawler._extract_post_id("") is None

    def test_extract_price(self, crawler):
        """_extract_price가 .hotdeal_info에서 가격을 추출해야 함"""
        html = """
        <div class="hotdeal_info">
            <span>가격: <a href="#">15,000원</a></span>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        assert crawler._extract_price(soup) == "15,000원"

    def test_extract_meta_data(self, crawler):
        """_extract_meta_data가 쇼핑몰 및 배송 정보를 추출해야 함"""
        html = """
        <div class="hotdeal_info">
            <span>쇼핑몰: <a href="#">G마켓</a></span>
            <span>배송: <a href="#">2,500원</a></span>
        </div>
        """
        soup = BeautifulSoup(html, "html.parser")
        meta_data = crawler._extract_meta_data(soup)
        assert "쇼핑몰: G마켓" in meta_data
        assert "배송: 2,500원" in meta_data
