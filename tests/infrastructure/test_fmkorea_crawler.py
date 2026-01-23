from unittest.mock import AsyncMock, MagicMock, patch

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
        """search_url 속성이 url과 동일해야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="맥북", client=mock_client)

        assert crawler.search_url == crawler.url


class TestFmkoreaCrawlerParse:
    """FmkoreaCrawler.parse() 메서드 테스트"""

    @pytest.fixture
    def sample_html(self):
        """FM코리아 핫딜 게시판 샘플 HTML (실제 구조: div.li)"""
        return """
        <div class="fm_best_widget">
            <div class="li">
                <div class="title">
                    <a href="/7953041">[11번가] 아이폰 15 프로 자급제 1,190,000원</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">11번가</a></span>
                    <span>가격: <a href="#">1,190,000원</a></span>
                    <span>배송: <a href="#">무료배송</a></span>
                </div>
            </div>
            <div class="li">
                <div class="title">
                    <a href="/7952999">[쿠팡] 맥북 에어 M3 15인치 1,490,000원</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">쿠팡</a></span>
                    <span>가격: <a href="#">1,490,000원</a></span>
                </div>
            </div>
            <div class="li hotdeal_var8Y">
                <div class="title">
                    <a href="/7950000">[종료] 에어팟 프로 2 품절</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">네이버</a></span>
                    <span>가격: <a href="#">299,000원</a></span>
                </div>
            </div>
        </div>
        """

    @pytest.fixture
    def sample_html_with_keyword(self):
        """키워드(아이폰)가 포함된 샘플 HTML"""
        return """
        <div class="fm_best_widget">
            <div class="li">
                <div class="title">
                    <a href="/7953041">[11번가] 아이폰 15 프로 자급제 1,190,000원</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">11번가</a></span>
                    <span>가격: <a href="#">1,190,000원</a></span>
                </div>
            </div>
            <div class="li">
                <div class="title">
                    <a href="/7952888">[쿠팡] 갤럭시 S24 울트라 할인</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">쿠팡</a></span>
                    <span>가격: <a href="#">1,299,000원</a></span>
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

    def test_parse_filters_by_keyword(self, crawler, sample_html_with_keyword):
        """parse()는 키워드가 포함된 게시물만 반환해야 함"""
        result = crawler.parse(sample_html_with_keyword)

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
        assert "7950000" not in ids

    def test_parse_returns_empty_list_when_no_content(self, crawler):
        """콘텐츠가 없으면 빈 리스트를 반환해야 함"""
        result = crawler.parse("<html><body>No content</body></html>")

        assert result == []

    def test_parse_returns_empty_when_keyword_not_found(self, crawler):
        """키워드가 없는 게시물만 있으면 빈 리스트를 반환해야 함"""
        html = """
        <div class="fm_best_widget">
            <div class="li">
                <div class="title">
                    <a href="/123456">[쿠팡] 갤럭시 S24 할인</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">쿠팡</a></span>
                </div>
            </div>
        </div>
        """
        result = crawler.parse(html)

        assert result == []


class TestFmkoreaCrawlerPagination:
    """FmkoreaCrawler 페이지네이션 테스트"""

    @pytest.fixture
    def crawler(self):
        """FmkoreaCrawler 인스턴스"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        return FmkoreaCrawler(keyword="아이폰", client=mock_client)

    def test_max_pages_default_value(self, crawler):
        """max_pages 기본값이 3이어야 함"""
        assert crawler.max_pages == 3

    def test_get_page_url_returns_first_page_url(self, crawler):
        """get_page_url(1)은 첫 페이지 URL을 반환해야 함"""
        url = crawler.get_page_url(1)
        assert url == "https://www.fmkorea.com/index.php?mid=hotdeal&page=1"

    def test_get_page_url_returns_correct_page_url(self, crawler):
        """get_page_url(N)은 해당 페이지 URL을 반환해야 함"""
        assert crawler.get_page_url(2) == "https://www.fmkorea.com/index.php?mid=hotdeal&page=2"
        assert crawler.get_page_url(5) == "https://www.fmkorea.com/index.php?mid=hotdeal&page=5"

    def test_url_property_still_returns_base_url(self, crawler):
        """url 속성은 기본 URL을 반환해야 함 (하위 호환성)"""
        assert crawler.url == "https://www.fmkorea.com/hotdeal"

    def test_custom_max_pages(self):
        """max_pages를 커스텀 값으로 설정할 수 있어야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="테스트", client=mock_client, max_pages=5)

        assert crawler.max_pages == 5


class TestFmkoreaCrawlerFetchparse:
    """FmkoreaCrawler.fetchparse() 다중 페이지 테스트"""

    @pytest.fixture
    def sample_html_page1(self):
        """페이지 1 샘플 HTML (아이폰 포함)"""
        return """
        <div class="fm_best_widget">
            <div class="li">
                <div class="title">
                    <a href="/1001">[11번가] 아이폰 15 프로</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">11번가</a></span>
                    <span>가격: <a href="#">1,190,000원</a></span>
                </div>
            </div>
        </div>
        """

    @pytest.fixture
    def sample_html_page2(self):
        """페이지 2 샘플 HTML (아이폰 포함)"""
        return """
        <div class="fm_best_widget">
            <div class="li">
                <div class="title">
                    <a href="/2001">[쿠팡] 아이폰 14 할인</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">쿠팡</a></span>
                    <span>가격: <a href="#">990,000원</a></span>
                </div>
            </div>
        </div>
        """

    @pytest.fixture
    def sample_html_no_keyword(self):
        """키워드 없는 페이지 샘플 HTML"""
        return """
        <div class="fm_best_widget">
            <div class="li">
                <div class="title">
                    <a href="/3001">[네이버] 갤럭시 S24</a>
                </div>
                <div class="hotdeal_info">
                    <span>쇼핑몰: <a href="#">네이버</a></span>
                </div>
            </div>
        </div>
        """

    @pytest.mark.asyncio
    async def test_fetchparse_fetches_multiple_pages(
        self, sample_html_page1, sample_html_page2
    ):
        """fetchparse()는 max_pages만큼 페이지를 가져와야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="아이폰", client=mock_client, max_pages=2)

        # fetch 메서드를 mock하여 페이지별로 다른 HTML 반환
        call_count = 0

        async def mock_fetch(url, timeout=10):
            nonlocal call_count
            call_count += 1
            if "page=1" in url:
                return sample_html_page1
            elif "page=2" in url:
                return sample_html_page2
            return None

        with patch.object(crawler, "fetch", side_effect=mock_fetch):
            results = await crawler.fetchparse()

        # 2개 페이지에서 각각 1개씩, 총 2개 결과
        assert len(results) == 2
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_fetchparse_deduplicates_results(self, sample_html_page1):
        """fetchparse()는 중복 ID를 제거해야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="아이폰", client=mock_client, max_pages=2)

        # 두 페이지 모두 같은 ID 반환
        async def mock_fetch(url, timeout=10):
            return sample_html_page1

        with patch.object(crawler, "fetch", side_effect=mock_fetch):
            results = await crawler.fetchparse()

        # 중복 제거되어 1개만 반환
        assert len(results) == 1
        assert results[0].id == "1001"

    @pytest.mark.asyncio
    async def test_fetchparse_continues_on_page_failure(
        self, sample_html_page1, sample_html_page2
    ):
        """fetchparse()는 한 페이지가 실패해도 계속 진행해야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="아이폰", client=mock_client, max_pages=3)

        # 페이지 2는 실패
        async def mock_fetch(url, timeout=10):
            if "page=1" in url:
                return sample_html_page1
            elif "page=2" in url:
                return None  # 실패
            elif "page=3" in url:
                return sample_html_page2
            return None

        with patch.object(crawler, "fetch", side_effect=mock_fetch):
            results = await crawler.fetchparse()

        # 페이지 1과 3에서 결과 수집
        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_fetchparse_returns_empty_when_no_matches(
        self, sample_html_no_keyword
    ):
        """fetchparse()는 매칭되는 키워드가 없으면 빈 리스트를 반환해야 함"""
        from app.src.Infrastructure.crawling.crawlers.fmkorea import FmkoreaCrawler

        mock_client = MagicMock()
        crawler = FmkoreaCrawler(keyword="아이폰", client=mock_client, max_pages=2)

        async def mock_fetch(url, timeout=10):
            return sample_html_no_keyword

        with patch.object(crawler, "fetch", side_effect=mock_fetch):
            results = await crawler.fetchparse()

        assert results == []


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
