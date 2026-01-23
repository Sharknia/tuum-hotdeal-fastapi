from unittest.mock import MagicMock

import pytest

from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.schemas import CrawledKeyword


class TestSiteNameRuliweb:
    """SiteName.RULIWEB enum 테스트"""

    def test_ruliweb_enum_exists(self):
        """SiteName에 RULIWEB이 정의되어 있어야 함"""
        assert hasattr(SiteName, "RULIWEB")
        assert SiteName.RULIWEB.value == "ruliweb"


class TestRuliwebCrawlerProperties:
    """RuliwebCrawler 속성 테스트"""

    def test_url_property(self):
        """url 속성이 올바른 검색 URL을 반환해야 함"""
        from app.src.Infrastructure.crawling.crawlers.ruliweb import RuliwebCrawler

        mock_client = MagicMock()
        crawler = RuliwebCrawler(keyword="스위치", client=mock_client)

        assert crawler.url == "https://bbs.ruliweb.com/market/board/1020?search_type=subject&search_key=스위치"

    def test_site_name_property(self):
        """site_name 속성이 SiteName.RULIWEB을 반환해야 함"""
        from app.src.Infrastructure.crawling.crawlers.ruliweb import RuliwebCrawler

        mock_client = MagicMock()
        crawler = RuliwebCrawler(keyword="테스트", client=mock_client)

        assert crawler.site_name == SiteName.RULIWEB

    def test_search_url_property(self):
        """search_url 속성이 url과 동일해야 함"""
        from app.src.Infrastructure.crawling.crawlers.ruliweb import RuliwebCrawler

        mock_client = MagicMock()
        crawler = RuliwebCrawler(keyword="아이폰", client=mock_client)

        assert crawler.search_url == crawler.url


class TestRuliwebCrawlerParse:
    """RuliwebCrawler.parse() 메서드 테스트"""

    @pytest.fixture
    def sample_html(self):
        """루리웹 핫딜 게시판 샘플 HTML"""
        return """
        <table class="board_list_table">
            <tr class="table_body notice">
                <td class="id">공지</td>
                <td class="subject"><a class="subject_link">공지사항</a></td>
            </tr>
            <tr class="table_body blocktarget">
                <td class="id">101141</td>
                <td class="divsn text_over">
                    <a href="#">게임S/W</a>
                </td>
                <td class="subject">
                    <div class="relative">
                        <a class="subject_link deco" href="https://bbs.ruliweb.com/market/board/1020/read/101141">
                            [컴퓨존] 닌텐도 스위치2 마리오카트 월드 세트 643,900원
                            <span class="num_reply">(47)</span>
                        </a>
                    </div>
                </td>
                <td class="writer text_over">닉이있을리가</td>
                <td class="recomd">11</td>
                <td class="hit">17685</td>
                <td class="time">14:54</td>
            </tr>
            <tr class="table_body blocktarget">
                <td class="id">101115</td>
                <td class="divsn text_over">
                    <a href="#">게임S/W</a>
                </td>
                <td class="subject">
                    <div class="relative">
                        <a class="subject_link deco" href="https://bbs.ruliweb.com/market/board/1020/read/101115">
                            [네이버] 닌텐도 스위치 타이틀 할인 / 가격 다양
                            <span class="num_reply">(30)</span>
                        </a>
                    </div>
                </td>
                <td class="writer text_over">내 아임다</td>
                <td class="recomd">31</td>
                <td class="hit">62525</td>
                <td class="time">2026.01.22</td>
            </tr>
            <tr class="table_body best inside blocktarget">
                <td class="id">베스트</td>
                <td class="subject"><a class="subject_link">베스트 글</a></td>
            </tr>
        </table>
        """

    @pytest.fixture
    def crawler(self):
        """RuliwebCrawler 인스턴스"""
        from app.src.Infrastructure.crawling.crawlers.ruliweb import RuliwebCrawler

        mock_client = MagicMock()
        return RuliwebCrawler(keyword="스위치", client=mock_client)

    def test_parse_returns_list_of_crawled_keywords(self, crawler, sample_html):
        """parse()는 CrawledKeyword 리스트를 반환해야 함"""
        result = crawler.parse(sample_html)

        assert isinstance(result, list)
        assert len(result) == 2  # notice, best 제외
        assert all(isinstance(item, CrawledKeyword) for item in result)

    def test_parse_extracts_correct_id(self, crawler, sample_html):
        """parse()는 게시물 ID를 올바르게 추출해야 함"""
        result = crawler.parse(sample_html)

        assert result[0].id == "101141"
        assert result[1].id == "101115"

    def test_parse_extracts_correct_title(self, crawler, sample_html):
        """parse()는 제목을 올바르게 추출해야 함 (댓글 수 제외)"""
        result = crawler.parse(sample_html)

        assert "[컴퓨존] 닌텐도 스위치2 마리오카트 월드 세트 643,900원" in result[0].title
        assert "(47)" not in result[0].title

    def test_parse_extracts_correct_link(self, crawler, sample_html):
        """parse()는 링크를 올바르게 추출해야 함"""
        result = crawler.parse(sample_html)

        assert result[0].link == "https://bbs.ruliweb.com/market/board/1020/read/101141"
        assert result[1].link == "https://bbs.ruliweb.com/market/board/1020/read/101115"

    def test_parse_sets_site_name(self, crawler, sample_html):
        """parse()는 site_name을 설정해야 함"""
        result = crawler.parse(sample_html)

        assert result[0].site_name == SiteName.RULIWEB

    def test_parse_sets_search_url(self, crawler, sample_html):
        """parse()는 search_url을 설정해야 함"""
        result = crawler.parse(sample_html)

        assert result[0].search_url == crawler.search_url

    def test_parse_excludes_notice_and_best(self, crawler, sample_html):
        """parse()는 공지사항과 베스트 글을 제외해야 함"""
        result = crawler.parse(sample_html)

        ids = [item.id for item in result]
        assert "공지" not in ids
        assert "베스트" not in ids

    def test_parse_returns_empty_list_when_no_table(self, crawler):
        """테이블이 없으면 빈 리스트를 반환해야 함"""
        result = crawler.parse("<html><body>No table</body></html>")

        assert result == []


class TestRuliwebRegistry:
    """RuliwebCrawler 레지스트리 등록 테스트"""

    def test_ruliweb_registered_in_registry(self):
        """RULIWEB이 레지스트리에 등록되어 있어야 함"""
        from app.src.Infrastructure.crawling.crawlers import CRAWLER_REGISTRY
        from app.src.Infrastructure.crawling.crawlers.ruliweb import RuliwebCrawler

        assert SiteName.RULIWEB in CRAWLER_REGISTRY
        assert CRAWLER_REGISTRY[SiteName.RULIWEB] is RuliwebCrawler

    def test_get_crawler_returns_ruliweb_crawler(self):
        """get_crawler로 RuliwebCrawler 인스턴스를 생성할 수 있어야 함"""
        from app.src.Infrastructure.crawling.crawlers import get_crawler
        from app.src.Infrastructure.crawling.crawlers.ruliweb import RuliwebCrawler

        mock_client = MagicMock()
        crawler = get_crawler(SiteName.RULIWEB, "테스트키워드", mock_client)

        assert isinstance(crawler, RuliwebCrawler)
        assert crawler.keyword == "테스트키워드"

    def test_get_active_sites_includes_ruliweb(self):
        """get_active_sites에 RULIWEB이 포함되어야 함"""
        from app.src.Infrastructure.crawling.crawlers import get_active_sites

        active_sites = get_active_sites()

        assert SiteName.RULIWEB in active_sites
