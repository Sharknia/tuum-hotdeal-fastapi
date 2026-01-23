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

    def test_url_property(self):
        """url 속성이 올바른 핫딜 게시판 URL을 반환해야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="아이폰", client=mock_client)

        assert crawler.url == "https://www.fmkorea.com/hotdeal"

    def test_site_name_property(self):
        """site_name 속성이 SiteName.FMKOREA를 반환해야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="테스트", client=mock_client)

        assert crawler.site_name == SiteName.FMKOREA

    def test_search_url_property(self):
        """search_url 속성이 url과 동일해야 함 (FM코리아는 검색 URL이 따로 없음)"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="맥북", client=mock_client)

        assert crawler.search_url == crawler.url


class TestFmkoreaCrawlerParse:
    """FmkoreaCrawler.parse() 메서드 테스트"""

    @pytest.fixture
    def sample_html(self):
        """FM코리아 핫딜 게시판 샘플 HTML"""
        return """
        <div id="content">
            <div class="fm_best_widget">
                <ul>
                    <li>
                        <div class="title">
                            <a href="/7953041">[11번가] 아이폰 15 프로 자급제 1,190,000원</a>
                        </div>
                        <div class="category">
                            <a href="#">디지털</a>
                        </div>
                        <div class="author">/ 핫딜러123</div>
                        <span class="pc_voted_count">
                            <span class="count">42</span>
                        </span>
                        <span class="comment_count">[15]</span>
                        <div class="hotdeal_info">
                            <span>쇼핑몰: <a href="#">11번가</a></span>
                            <span>가격: <a href="#">1,190,000원</a></span>
                            <span>배송: <a href="#">무료배송</a></span>
                        </div>
                    </li>
                    <li>
                        <div class="title">
                            <a href="/7952999">[쿠팡] 맥북 에어 M3 15인치 1,490,000원</a>
                        </div>
                        <div class="category">
                            <a href="#">디지털</a>
                        </div>
                        <div class="author">/ 딜마스터</div>
                        <div class="hotdeal_info">
                            <span>쇼핑몰: <a href="#">쿠팡</a></span>
                            <span>가격: <a href="#">1,490,000원</a></span>
                        </div>
                    </li>
                    <li class="hotdeal_var8Y">
                        <div class="title">
                            <a href="/7950000">[종료] 에어팟 프로 2 품절</a>
                        </div>
                        <div class="category">
                            <a href="#">디지털</a>
                        </div>
                        <div class="author">/ 테스터</div>
                        <div class="hotdeal_info">
                            <span>쇼핑몰: <a href="#">네이버</a></span>
                            <span>가격: <a href="#">299,000원</a></span>
                        </div>
                    </li>
                </ul>
            </div>
        </div>
        """

    @pytest.fixture
    def sample_html_with_keyword(self):
        """키워드(아이폰)가 포함된 샘플 HTML"""
        return """
        <div id="content">
            <div class="fm_best_widget">
                <ul>
                    <li>
                        <div class="title">
                            <a href="/7953041">[11번가] 아이폰 15 프로 자급제 1,190,000원</a>
                        </div>
                        <div class="category">
                            <a href="#">디지털</a>
                        </div>
                        <div class="author">/ 핫딜러123</div>
                        <div class="hotdeal_info">
                            <span>쇼핑몰: <a href="#">11번가</a></span>
                            <span>가격: <a href="#">1,190,000원</a></span>
                        </div>
                    </li>
                    <li>
                        <div class="title">
                            <a href="/7952888">[쿠팡] 갤럭시 S24 울트라 할인</a>
                        </div>
                        <div class="category">
                            <a href="#">디지털</a>
                        </div>
                        <div class="author">/ 딜러</div>
                        <div class="hotdeal_info">
                            <span>쇼핑몰: <a href="#">쿠팡</a></span>
                            <span>가격: <a href="#">1,299,000원</a></span>
                        </div>
                    </li>
                </ul>
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

    def test_parse_filters_by_keyword(self, crawler, sample_html_with_keyword):
        """parse()는 키워드가 포함된 게시물만 반환해야 함"""
        result = crawler.parse(sample_html_with_keyword)

        # "아이폰" 키워드가 포함된 게시물만 반환
        assert len(result) == 1
        assert "아이폰" in result[0].title

    def test_parse_extracts_correct_id(self, crawler, sample_html_with_keyword):
        """parse()는 게시물 ID를 올바르게 추출해야 함"""
        result = crawler.parse(sample_html_with_keyword)

        assert result[0].id == "7953041"

    def test_parse_extracts_correct_title(self, crawler, sample_html_with_keyword):
        """parse()는 제목을 올바르게 추출해야 함"""
        result = crawler.parse(sample_html_with_keyword)

        assert "[11번가] 아이폰 15 프로 자급제 1,190,000원" in result[0].title

    def test_parse_extracts_correct_link(self, crawler, sample_html_with_keyword):
        """parse()는 링크를 올바르게 추출해야 함"""
        result = crawler.parse(sample_html_with_keyword)

        assert result[0].link == "https://www.fmkorea.com/7953041"

    def test_parse_extracts_price_from_hotdeal_info(self, crawler, sample_html_with_keyword):
        """parse()는 hotdeal_info에서 가격을 추출해야 함"""
        result = crawler.parse(sample_html_with_keyword)

        assert result[0].price == "1,190,000원"

    def test_parse_sets_site_name(self, crawler, sample_html_with_keyword):
        """parse()는 site_name을 설정해야 함"""
        result = crawler.parse(sample_html_with_keyword)

        assert result[0].site_name == SiteName.FMKOREA

    def test_parse_sets_search_url(self, crawler, sample_html_with_keyword):
        """parse()는 search_url을 설정해야 함"""
        result = crawler.parse(sample_html_with_keyword)

        assert result[0].search_url == crawler.search_url

    def test_parse_excludes_ended_deals(self, crawler, sample_html):
        """parse()는 종료된 핫딜(hotdeal_var8Y)을 제외해야 함"""
        result = crawler.parse(sample_html)

        ids = [item.id for item in result]
        assert "7950000" not in ids  # 종료된 딜 ID

    def test_parse_returns_empty_list_when_no_content(self, crawler):
        """콘텐츠가 없으면 빈 리스트를 반환해야 함"""
        result = crawler.parse("<html><body>No content</body></html>")

        assert result == []

    def test_parse_returns_empty_when_keyword_not_found(self, crawler):
        """키워드가 없는 게시물만 있으면 빈 리스트를 반환해야 함"""
        html = """
        <div id="content">
            <div class="fm_best_widget">
                <ul>
                    <li>
                        <div class="title">
                            <a href="/123456">[쿠팡] 갤럭시 S24 할인</a>
                        </div>
                        <div class="category"><a href="#">디지털</a></div>
                        <div class="author">/ 테스터</div>
                        <div class="hotdeal_info">
                            <span>쇼핑몰: <a href="#">쿠팡</a></span>
                        </div>
                    </li>
                </ul>
            </div>
        </div>
        """
        result = crawler.parse(html)

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
