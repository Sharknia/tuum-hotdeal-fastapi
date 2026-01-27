from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.models import Keyword, KeywordSite
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.worker_main import get_new_hotdeal_keywords_for_site


def mock_crawled_list(ids):
    return [
        CrawledKeyword(
            id=id_str,
            title=f"Title {id_str}",
            link=f"http://example.com/{id_str}",
            price="1000",
            meta_data="site:test",
            site_name=SiteName.ALGUMON,
            search_url="http://example.com/search"
        )
        for id_str in ids
    ]

class TestMultiAnchor:
    @pytest.mark.asyncio
    async def test_legacy_single_id(self):
        """stored="100", fetched=["100"], expected=[]"""
        session = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.add = MagicMock()
        keyword = MagicMock(spec=Keyword)
        keyword.id = 1
        keyword.title = "test"
        client = AsyncMock()
        site = SiteName.ALGUMON

        last_crawled_site = MagicMock(spec=KeywordSite)
        last_crawled_site.external_id = "100"

        mock_result = MagicMock()
        mock_result.scalars().one_or_none.return_value = last_crawled_site
        session.execute.return_value = mock_result

        crawler = AsyncMock()
        crawler.fetchparse.return_value = mock_crawled_list(["100"])

        with patch("app.worker_main.get_crawler", return_value=crawler):
            new_deals = await get_new_hotdeal_keywords_for_site(session, keyword, client, site)
            assert len(new_deals) == 0

    @pytest.mark.asyncio
    async def test_multi_anchor_normal(self):
        """stored="100,99,98", fetched=["100"], expected=[]"""
        session = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.add = MagicMock()
        keyword = MagicMock(spec=Keyword)
        keyword.id = 1
        keyword.title = "test"
        client = AsyncMock()
        site = SiteName.ALGUMON

        last_crawled_site = MagicMock(spec=KeywordSite)
        last_crawled_site.external_id = "100,99,98"

        mock_result = MagicMock()
        mock_result.scalars().one_or_none.return_value = last_crawled_site
        session.execute.return_value = mock_result

        crawler = AsyncMock()
        crawler.fetchparse.return_value = mock_crawled_list(["100"])

        with patch("app.worker_main.get_crawler", return_value=crawler):
            new_deals = await get_new_hotdeal_keywords_for_site(session, keyword, client, site)
            assert len(new_deals) == 0

    @pytest.mark.asyncio
    async def test_multi_anchor_new(self):
        """stored="100,99,98", fetched=["101","100"], expected=["101"]"""
        session = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.add = MagicMock()
        keyword = MagicMock(spec=Keyword)
        keyword.id = 1
        keyword.title = "test"
        client = AsyncMock()
        site = SiteName.ALGUMON

        last_crawled_site = MagicMock(spec=KeywordSite)
        last_crawled_site.external_id = "100,99,98"

        mock_result = MagicMock()
        mock_result.scalars().one_or_none.return_value = last_crawled_site
        session.execute.return_value = mock_result

        crawler = AsyncMock()
        crawler.fetchparse.return_value = mock_crawled_list(["101", "100"])

        with patch("app.worker_main.get_crawler", return_value=crawler):
            new_deals = await get_new_hotdeal_keywords_for_site(session, keyword, client, site)
            assert len(new_deals) == 1
            assert new_deals[0].id == "101"

    @pytest.mark.asyncio
    async def test_multi_anchor_deletion_1(self):
        """stored="100,99,98", fetched=["101","99"], expected=["101"]. (100 deleted)."""
        session = AsyncMock()
        keyword = MagicMock(spec=Keyword)
        keyword.id = 1
        keyword.title = "test"
        client = AsyncMock()
        site = SiteName.ALGUMON

        last_crawled_site = MagicMock(spec=KeywordSite)
        last_crawled_site.external_id = "100,99,98"

        mock_result = MagicMock()
        mock_result.scalars().one_or_none.return_value = last_crawled_site
        session.execute.return_value = mock_result

        crawler = AsyncMock()
        crawler.fetchparse.return_value = mock_crawled_list(["101", "99"])

        with patch("app.worker_main.get_crawler", return_value=crawler):
            new_deals = await get_new_hotdeal_keywords_for_site(session, keyword, client, site)
            assert len(new_deals) == 1
            assert new_deals[0].id == "101"

    @pytest.mark.asyncio
    async def test_multi_anchor_deletion_2(self):
        """stored="100,99,98", fetched=["101","98"], expected=["101"]. (100, 99 deleted)."""
        session = AsyncMock()
        keyword = MagicMock(spec=Keyword)
        keyword.id = 1
        keyword.title = "test"
        client = AsyncMock()
        site = SiteName.ALGUMON

        last_crawled_site = MagicMock(spec=KeywordSite)
        last_crawled_site.external_id = "100,99,98"

        mock_result = MagicMock()
        mock_result.scalars().one_or_none.return_value = last_crawled_site
        session.execute.return_value = mock_result

        crawler = AsyncMock()
        crawler.fetchparse.return_value = mock_crawled_list(["101", "98"])

        with patch("app.worker_main.get_crawler", return_value=crawler):
            new_deals = await get_new_hotdeal_keywords_for_site(session, keyword, client, site)
            assert len(new_deals) == 1
            assert new_deals[0].id == "101"

    @pytest.mark.asyncio
    async def test_multi_anchor_all_missing(self):
        """stored="100,99,98", fetched=["105"], expected=["105"]. (All missing -> Fetch All)."""
        session = AsyncMock()
        keyword = MagicMock(spec=Keyword)
        keyword.id = 1
        keyword.title = "test"
        client = AsyncMock()
        site = SiteName.ALGUMON

        last_crawled_site = MagicMock(spec=KeywordSite)
        last_crawled_site.external_id = "100,99,98"

        mock_result = MagicMock()
        mock_result.scalars().one_or_none.return_value = last_crawled_site
        session.execute.return_value = mock_result

        crawler = AsyncMock()
        crawler.fetchparse.return_value = mock_crawled_list(["105"])

        with patch("app.worker_main.get_crawler", return_value=crawler):
            new_deals = await get_new_hotdeal_keywords_for_site(session, keyword, client, site)
            assert len(new_deals) == 1
            assert new_deals[0].id == "105"

    @pytest.mark.asyncio
    async def test_multi_anchor_save_format(self):
        """Verify DB update calls session.add with CSV "id1,id2,id3"."""
        session = MagicMock()
        session.execute = AsyncMock()
        session.commit = AsyncMock()
        session.add = MagicMock()
        keyword = MagicMock(spec=Keyword)
        keyword.id = 1
        keyword.title = "test"
        client = AsyncMock()
        site = SiteName.ALGUMON

        mock_result = MagicMock()
        mock_result.scalars().one_or_none.return_value = None
        session.execute.return_value = mock_result

        crawler = AsyncMock()
        crawler.fetchparse.return_value = mock_crawled_list(["102", "101", "100"])

        with patch("app.worker_main.get_crawler", return_value=crawler):
            await get_new_hotdeal_keywords_for_site(session, keyword, client, site)

            assert session.add.called
            added_obj = session.add.call_args[0][0]
            assert isinstance(added_obj, KeywordSite)
            assert added_obj.external_id == "102,101,100"
