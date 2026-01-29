from app.src.domain.hotdeal.enums import SiteName


class TestGetSiteInfoList:
    def test_get_site_info_list_returns_list(self):
        # given
        from app.src.Infrastructure.crawling.crawlers import get_site_info_list

        # when
        result = get_site_info_list()

        # then
        assert isinstance(result, list)
        assert len(result) > 0

    def test_get_site_info_list_contains_all_active_sites(self):
        # given
        from app.src.Infrastructure.crawling.crawlers import (
            get_active_sites,
            get_site_info_list,
        )

        # when
        site_info_list = get_site_info_list()
        active_sites = get_active_sites()

        # then
        site_names = [info.name for info in site_info_list]
        for site in active_sites:
            assert site in site_names

    def test_site_info_has_required_fields(self):
        # given
        from app.src.Infrastructure.crawling.crawlers import get_site_info_list

        # when
        result = get_site_info_list()

        # then
        for site_info in result:
            assert hasattr(site_info, "name")
            assert hasattr(site_info, "display_name")
            assert hasattr(site_info, "search_url_template")
            assert isinstance(site_info.name, SiteName)
            assert isinstance(site_info.display_name, str)
            assert isinstance(site_info.search_url_template, str)

    def test_search_url_template_contains_keyword_placeholder(self):
        # given
        from app.src.Infrastructure.crawling.crawlers import get_site_info_list

        # when
        result = get_site_info_list()

        # then
        for site_info in result:
            assert "{keyword}" in site_info.search_url_template

    def test_algumon_site_info(self):
        # given
        from app.src.Infrastructure.crawling.crawlers import get_site_info_list

        # when
        result = get_site_info_list()
        algumon = next((s for s in result if s.name == SiteName.ALGUMON), None)

        # then
        assert algumon is not None
        assert algumon.display_name == "알구몬"
        assert "algumon.com" in algumon.search_url_template

    def test_ruliweb_not_in_site_info_list(self):
        """Ruliweb 크롤러가 제거되었으므로 site_info_list에 포함되지 않아야 함"""
        # given
        from app.src.Infrastructure.crawling.crawlers import get_site_info_list

        # when
        result = get_site_info_list()
        ruliweb = next((s for s in result if s.name == SiteName.RULIWEB), None)

        # then
        assert ruliweb is None, "Ruliweb은 크롤러 레지스트리에서 제거되었으므로 site_info_list에 포함되지 않아야 함"
