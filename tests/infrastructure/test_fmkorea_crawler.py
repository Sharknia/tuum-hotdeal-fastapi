from unittest.mock import MagicMock

import pytest

from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword


class TestSiteNameFmkorea:
    """SiteName.FMKOREA enum 테스트"""

    def test_fmkorea_enum_exists(self):
        """SiteName에 FMKOREA가 정의되어 있어야 함"""
        assert hasattr(SiteName, "FMKOREA")
        assert SiteName.FMKOREA.value == "fmKorea"


class TestFmkoreaCrawlerProperties:
    """FmkoreaCrawler 속성 테스트"""

    def test_requires_browser_is_true(self):
        """FmkoreaCrawler는 requires_browser=True여야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="테스트", client=mock_client)

        assert crawler.requires_browser is True

    def test_url_property_returns_search_url(self):
        """url 속성이 검색 URL을 반환해야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="아이폰", client=mock_client)

        expected = "https://www.fmkorea.com/search.php?mid=hotdeal&search_keyword=%EC%95%84%EC%9D%B4%ED%8F%B0&search_target=title_content"
        assert crawler.url == expected

    def test_url_property_encodes_keyword(self):
        """url 속성이 키워드를 URL 인코딩해야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="맥북 프로", client=mock_client)

        assert "search_keyword=" in crawler.url
        assert "%EB%A7%A5%EB%B6%81" in crawler.url  # 맥북
        assert "%ED%94%84%EB%A1%9C" in crawler.url  # 프로

    def test_site_name_property(self):
        """site_name 속성이 SiteName.FMKOREA를 반환해야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="테스트", client=mock_client)

        assert crawler.site_name == SiteName.FMKOREA

    def test_search_url_property(self):
        """search_url 속성이 url과 동일해야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="맥북", client=mock_client)

        assert crawler.search_url == crawler.url


class TestFmkoreaCrawlerParse:
    """FmkoreaCrawler.parse() 메서드 테스트"""

    @pytest.fixture
    def sample_html(self):
        """FM코리아 검색 결과 샘플 HTML (검색 결과 페이지 형식)"""
        return """
        <div class="fm_best_widget">
            <div class="li">
                <div class="title">
                    <a href="/index.php?mid=hotdeal&amp;document_srl=7953041&amp;search_keyword=test">[11번가] 아이폰 15 프로 자급제 1,190,000원</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">11번가</a></span>
                    <span>가격: <a href="#">1,190,000원</a></span>
                    <span>배송: <a href="#">무료배송</a></span>
                </div>
            </div>
            <div class="li">
                <div class="title">
                    <a href="/index.php?mid=hotdeal&amp;document_srl=7952999&amp;search_keyword=test">[쿠팡] 아이폰 14 할인</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">쿠팡</a></span>
                    <span>가격: <a href="#">990,000원</a></span>
                </div>
            </div>
            <div class="li hotdeal_var8Y">
                <div class="title">
                    <a href="/index.php?mid=hotdeal&amp;document_srl=7950000&amp;search_keyword=test">[종료] 아이폰 13 품절</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">네이버</a></span>
                    <span>가격: <a href="#">299,000원</a></span>
                </div>
            </div>
        </div>
        """

    @pytest.fixture
    def crawler(self):
        """FmkoreaCrawler 인스턴스"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        return FmkoreaCrawler(keyword="아이폰", client=mock_client)

    def test_parse_returns_list_of_crawled_keywords(self, crawler, sample_html):
        """parse()는 CrawledKeyword 리스트를 반환해야 함"""
        result = crawler.parse(sample_html)

        assert isinstance(result, list)
        assert all(isinstance(item, CrawledKeyword) for item in result)

    def test_parse_extracts_all_matching_items(self, crawler, sample_html):
        """parse()는 검색 결과의 모든 아이템을 반환해야 함 (종료된 딜 제외)"""
        result = crawler.parse(sample_html)

        assert len(result) == 2
        assert all("아이폰" in item.title for item in result)

    def test_parse_extracts_correct_id(self, crawler, sample_html):
        """parse()는 게시물 ID를 올바르게 추출해야 함"""
        result = crawler.parse(sample_html)

        assert result[0].id == "7953041"
        assert result[1].id == "7952999"

    def test_parse_extracts_correct_title(self, crawler, sample_html):
        """parse()는 제목을 올바르게 추출해야 함"""
        result = crawler.parse(sample_html)

        assert "[11번가] 아이폰 15 프로 자급제 1,190,000원" in result[0].title

    def test_parse_extracts_correct_link(self, crawler, sample_html):
        """parse()는 링크를 올바르게 추출해야 함"""
        result = crawler.parse(sample_html)

        assert result[0].link == "https://www.fmkorea.com/7953041"

    def test_parse_extracts_price_from_hotdeal_info(self, crawler, sample_html):
        """parse()는 hotdeal_info에서 가격을 추출해야 함"""
        result = crawler.parse(sample_html)

        assert result[0].price == "1,190,000원"

    def test_parse_sets_site_name(self, crawler, sample_html):
        """parse()는 site_name을 설정해야 함"""
        result = crawler.parse(sample_html)

        assert result[0].site_name == SiteName.FMKOREA

    def test_parse_sets_search_url(self, crawler, sample_html):
        """parse()는 search_url을 설정해야 함"""
        result = crawler.parse(sample_html)

        assert result[0].search_url == crawler.search_url

    def test_parse_excludes_ended_deals(self, crawler, sample_html):
        """parse()는 종료된 핫딜(hotdeal_var8Y)을 제외해야 함"""
        result = crawler.parse(sample_html)

        ids = [item.id for item in result]
        assert "7950000" not in ids

    def test_parse_returns_empty_list_when_no_content(self, crawler):
        """콘텐츠가 없으면 빈 리스트를 반환해야 함"""
        result = crawler.parse("<html><body>No content</body></html>")

        assert result == []


class TestFmkoreaRegistry:
    """FmkoreaCrawler 레지스트리 등록 테스트"""

    def test_fmkorea_registered_in_registry(self):
        """FMKOREA가 레지스트리에 등록되어 있어야 함"""
        from app.src.Infrastructure.crawling.crawlers import CRAWLER_REGISTRY
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        assert SiteName.FMKOREA in CRAWLER_REGISTRY
        assert CRAWLER_REGISTRY[SiteName.FMKOREA] is FmkoreaCrawler

    def test_get_crawler_returns_fmkorea_crawler(self):
        """get_crawler로 FmkoreaCrawler 인스턴스를 생성할 수 있어야 함"""
        from app.src.Infrastructure.crawling.crawlers import get_crawler
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = get_crawler(SiteName.FMKOREA, "테스트키워드", mock_client)

        assert isinstance(crawler, FmkoreaCrawler)
        assert crawler.keyword == "테스트키워드"

    def test_get_active_sites_includes_fmkorea(self):
        """get_active_sites에 FMKOREA가 포함되어야 함"""
        from app.src.Infrastructure.crawling.crawlers import get_active_sites

        active_sites = get_active_sites()

        assert SiteName.FMKOREA in active_sites
