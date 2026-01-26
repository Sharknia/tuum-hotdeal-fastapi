from unittest.mock import AsyncMock, patch

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.models import Keyword, KeywordSite
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.worker_main import (
    get_new_hotdeal_keywords,
    get_new_hotdeal_keywords_for_site,
    handle_keyword,
    job,
)

# --- 테스트 데이터 ---

CRAWLED_DATA_NEW = [
    CrawledKeyword(
        id="101",
        title="[새상품] 키보드",
        link="new_link1",
        price="10000원",
        site_name=SiteName.ALGUMON,
        search_url="https://www.algumon.com/search/테스트키워드",
    ),
    CrawledKeyword(
        id="102",
        title="[새상품] 마우스",
        link="new_link2",
        price="20000원",
        site_name=SiteName.ALGUMON,
        search_url="https://www.algumon.com/search/테스트키워드",
    ),
    CrawledKeyword(
        id="103",
        title="[기존상품] 모니터",
        link="old_link3",
        price="30000원",
        site_name=SiteName.ALGUMON,
        search_url="https://www.algumon.com/search/테스트키워드",
    ),
]

CRAWLED_DATA_NO_NEW = [
    CrawledKeyword(
        id="103",
        title="[기존상품] 모니터",
        link="old_link3",
        price="30000원",
        site_name=SiteName.ALGUMON,
        search_url="https://www.algumon.com/search/테스트키워드",
    ),
    CrawledKeyword(
        id="104",
        title="[기존상품] 스피커",
        link="old_link4",
        price="40000원",
        site_name=SiteName.ALGUMON,
        search_url="https://www.algumon.com/search/테스트키워드",
    ),
]


# --- 테스트 픽스처 ---


@pytest.fixture
async def keyword_in_db(mock_db_session: AsyncSession) -> Keyword:
    """테스트용 키워드를 DB에 생성하고 반환합니다."""
    keyword = Keyword(title="테스트키워드")
    mock_db_session.add(keyword)
    await mock_db_session.commit()
    await mock_db_session.refresh(keyword)
    return keyword


@pytest.fixture
async def keyword_and_site_in_db(
    mock_db_session: AsyncSession, keyword_in_db: Keyword
) -> tuple[Keyword, KeywordSite]:
    """테스트용 키워드와 이전에 크롤링된 사이트 정보를 DB에 생성하고 반환합니다."""
    keyword_site = KeywordSite(
        keyword_id=keyword_in_db.id,
        site_name=SiteName.ALGUMON,
        external_id="103",  # CRAWLED_DATA_NO_NEW의 첫 번째 항목과 일치
        link="old_link3",
        price="30000원",
    )
    mock_db_session.add(keyword_site)
    await mock_db_session.commit()
    await mock_db_session.refresh(keyword_site)
    return keyword_in_db, keyword_site


# --- 테스트 케이스 ---


@pytest.mark.asyncio
async def test_get_new_hotdeal_keywords_first_crawl(
    mock_db_session: AsyncSession, keyword_in_db: Keyword
):
    """
    시나리오 1: 키워드가 처음으로 크롤링될 때
    - 기대: 첫 크롤링 시 스팸 방지를 위해 최신 1개만 반환되고, DB에 저장되어야 함
    """
    # GIVEN: 크롤러가 CRAWLED_DATA_NEW를 반환하도록 모킹
    mock_crawler = AsyncMock()
    mock_crawler.fetchparse.return_value = CRAWLED_DATA_NEW

    with patch("app.worker_main.get_crawler", return_value=mock_crawler):
        async with httpx.AsyncClient() as client:
            # WHEN: 새로운 핫딜을 조회
            new_deals = await get_new_hotdeal_keywords(
                mock_db_session, keyword_in_db, client
            )

            # THEN: 첫 크롤링이므로 최신 1개만 반환되어야 함
            assert len(new_deals) == 1
            assert new_deals[0].id == "101"

            # AND: 첫 번째 결과가 DB에 저장되어야 함
            stmt = select(KeywordSite).where(KeywordSite.keyword_id == keyword_in_db.id)
            result = await mock_db_session.execute(stmt)
            saved_site = result.scalars().one()

            assert saved_site is not None
            assert saved_site.external_id == "101"


@pytest.mark.asyncio
async def test_get_new_hotdeal_keywords_no_new_deals(
    mock_db_session: AsyncSession, keyword_and_site_in_db: tuple[Keyword, KeywordSite]
):
    """
    시나리오 2: 새로운 핫딜이 없을 때
    - 기대: 빈 리스트가 반환되어야 함
    """
    # GIVEN: 크롤러가 이전에 저장된 핫딜과 동일한 목록을 반환하도록 모킹
    keyword, _ = keyword_and_site_in_db
    mock_crawler = AsyncMock()
    mock_crawler.fetchparse.return_value = CRAWLED_DATA_NO_NEW

    with patch("app.worker_main.get_crawler", return_value=mock_crawler):
        async with httpx.AsyncClient() as client:
            # WHEN: 새로운 핫딜을 조회
            new_deals = await get_new_hotdeal_keywords(mock_db_session, keyword, client)

            # THEN: 빈 리스트가 반환되어야 함
            assert len(new_deals) == 0


@pytest.mark.asyncio
async def test_get_new_hotdeal_keywords_with_new_deals(
    mock_db_session: AsyncSession, keyword_and_site_in_db: tuple[Keyword, KeywordSite]
):
    """
    시나리오 3: 새로운 핫딜이 발견되었을 때
    - 기대: 이전 핫딜 제외한 새 항목만 반환되고, DB는 최신 핫딜로 업데이트
    """
    # GIVEN: 크롤러가 새로운 핫딜이 포함된 목록을 반환하도록 모킹
    keyword, old_site_data = keyword_and_site_in_db
    mock_crawler = AsyncMock()
    mock_crawler.fetchparse.return_value = CRAWLED_DATA_NEW

    with patch("app.worker_main.get_crawler", return_value=mock_crawler):
        async with httpx.AsyncClient() as client:
            # WHEN: 새로운 핫딜을 조회
            new_deals = await get_new_hotdeal_keywords(mock_db_session, keyword, client)

            # THEN: 새로운 핫딜 2개만 반환되어야 함 (기존 103 제외)
            assert len(new_deals) == 2
            assert new_deals[0].id == "101"
            assert new_deals[1].id == "102"
            assert not any(deal.id == "103" for deal in new_deals)

            # AND: DB의 external_id가 새로운 핫딜의 ID로 업데이트되어야 함
            await mock_db_session.refresh(old_site_data)
            assert old_site_data.external_id == "101"


@pytest.mark.asyncio
async def test_job_e2e(mock_db_session, keyword_in_db):
    """E2E 테스트: job 함수가 올바르게 동작하는지 검증"""
    # GIVEN: DB에 사용자, 키워드, 사용자-키워드 관계 설정
    from app.src.domain.user.models import User

    user = User(
        email="test@example.com",
        nickname="testuser",
        hashed_password="hashed_password",
    )
    user.keywords.append(keyword_in_db)
    mock_db_session.add(user)
    await mock_db_session.commit()

    # GIVEN: 크롤링, 메일 발송, DB 조회 모킹
    with (
        patch(
            "app.worker_main.get_new_hotdeal_keywords_for_site", new_callable=AsyncMock
        ) as mock_get_new,
        patch(
            "app.worker_main.send_email", new_callable=AsyncMock
        ) as mock_send_email,
        patch("app.worker_main.AsyncSessionLocal", return_value=mock_db_session),
        patch("app.worker_main.settings.ENVIRONMENT", "prod"),
        patch("app.worker_main.SharedBrowser") as mock_shared,
    ):
        mock_shared.get_instance.return_value.start = AsyncMock()
        mock_shared.get_instance.return_value.stop = AsyncMock()
        mock_get_new.return_value = CRAWLED_DATA_NEW
        mock_send_email.return_value = None

        # WHEN: job 실행
        await job()

        # THEN: 메일 발송 함수가 올바른 인자와 함께 1회 호출되었는지 확인
        mock_send_email.assert_called_once()
        args, kwargs = mock_send_email.call_args
        assert kwargs["to"] == "test@example.com"
        assert "테스트키워드" in kwargs["subject"]
        assert "[새상품] 키보드" in kwargs["body"]


# --- Phase 3: 멀티사이트 지원 테스트 ---


@pytest.mark.asyncio
async def test_get_new_hotdeal_keywords_for_site_first_crawl(
    mock_db_session: AsyncSession, keyword_in_db: Keyword
):
    """
    시나리오: 특정 사이트에서 처음 크롤링
    - 기대: 최신 1개만 반환, DB에 저장
    """
    # GIVEN: get_crawler가 모킹된 크롤러를 반환하도록 설정
    mock_crawler = AsyncMock()
    mock_crawler.fetchparse.return_value = CRAWLED_DATA_NEW

    with patch("app.worker_main.get_crawler", return_value=mock_crawler):
        async with httpx.AsyncClient() as client:
            # WHEN: 특정 사이트에서 새로운 핫딜 조회
            new_deals = await get_new_hotdeal_keywords_for_site(
                mock_db_session, keyword_in_db, client, SiteName.ALGUMON
            )

            # THEN: 첫 크롤링이므로 최신 1개만 반환
            assert len(new_deals) == 1
            assert new_deals[0].id == "101"

            # AND: DB에 저장 확인
            stmt = select(KeywordSite).where(
                KeywordSite.keyword_id == keyword_in_db.id,
                KeywordSite.site_name == SiteName.ALGUMON,
            )
            result = await mock_db_session.execute(stmt)
            saved_site = result.scalars().one()
            assert saved_site.external_id == "101"


@pytest.mark.asyncio
async def test_get_new_hotdeal_keywords_for_site_with_new_deals(
    mock_db_session: AsyncSession, keyword_and_site_in_db: tuple[Keyword, KeywordSite]
):
    """
    시나리오: 특정 사이트에서 새로운 핫딜 발견
    - 기대: 이전 핫딜 제외, 새 항목만 반환
    """
    keyword, old_site_data = keyword_and_site_in_db

    mock_crawler = AsyncMock()
    mock_crawler.fetchparse.return_value = CRAWLED_DATA_NEW

    with patch("app.worker_main.get_crawler", return_value=mock_crawler):
        async with httpx.AsyncClient() as client:
            # WHEN: 새로운 핫딜 조회
            new_deals = await get_new_hotdeal_keywords_for_site(
                mock_db_session, keyword, client, SiteName.ALGUMON
            )

            # THEN: 새로운 핫딜 2개만 반환 (기존 103 제외)
            assert len(new_deals) == 2
            assert new_deals[0].id == "101"
            assert new_deals[1].id == "102"

            # AND: DB 업데이트 확인
            await mock_db_session.refresh(old_site_data)
            assert old_site_data.external_id == "101"


@pytest.mark.asyncio
async def test_handle_keyword_multisite_all_success(
    mock_db_session: AsyncSession, keyword_in_db: Keyword
):
    """
    시나리오: 모든 사이트에서 크롤링 성공
    - 기대: 모든 사이트의 결과가 병합되어 반환
    """
    import asyncio

    # GIVEN: 사이트별 세마포어 설정
    site_semaphores = {SiteName.ALGUMON: asyncio.Semaphore(2)}

    # GIVEN: get_new_hotdeal_keywords_for_site가 결과를 반환하도록 모킹
    with (
        patch("app.worker_main.get_active_sites", return_value=[SiteName.ALGUMON]),
        patch(
            "app.worker_main.get_new_hotdeal_keywords_for_site", new_callable=AsyncMock
        ) as mock_get_for_site,
        patch("app.worker_main.AsyncSessionLocal", return_value=mock_db_session),
    ):
        mock_get_for_site.return_value = CRAWLED_DATA_NEW[:2]

        async with httpx.AsyncClient() as client:
            # WHEN: handle_keyword 호출
            result = await handle_keyword(keyword_in_db, client, site_semaphores)

            # THEN: 결과가 반환되어야 함
            assert result is not None
            keyword, deals = result
            assert keyword.title == "테스트키워드"
            assert len(deals) == 2


@pytest.mark.asyncio
async def test_handle_keyword_multisite_partial_failure(
    mock_db_session: AsyncSession, keyword_in_db: Keyword
):
    """
    시나리오: 일부 사이트에서 크롤링 실패
    - 기대: 성공한 사이트의 결과만 반환, 실패 로깅
    """
    import asyncio

    # GIVEN: 가상의 두 사이트 설정 (ALGUMON + FMKOREA)
    # 참고: FMKOREA가 enum에 없을 수 있으므로 ALGUMON만 사용하되, 테스트용으로 같은 사이트 2번 호출 시뮬레이션
    site_semaphores = {SiteName.ALGUMON: asyncio.Semaphore(2)}

    call_count = 0

    async def mock_get_for_site_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return CRAWLED_DATA_NEW[:1]  # 첫 번째 호출: 성공
        else:
            raise Exception("Crawling failed")  # 두 번째 호출: 실패

    with (
        patch(
            "app.worker_main.get_active_sites",
            return_value=[SiteName.ALGUMON, SiteName.ALGUMON],  # 테스트용 중복
        ),
        patch(
            "app.worker_main.get_new_hotdeal_keywords_for_site", new_callable=AsyncMock
        ) as mock_get_for_site,
        patch("app.worker_main.AsyncSessionLocal", return_value=mock_db_session),
        patch("app.worker_main.logger") as mock_logger,
    ):
        mock_get_for_site.side_effect = mock_get_for_site_side_effect

        async with httpx.AsyncClient() as client:
            # WHEN: handle_keyword 호출
            result = await handle_keyword(keyword_in_db, client, site_semaphores)

            # THEN: 성공한 사이트의 결과만 반환
            assert result is not None
            keyword, deals = result
            assert len(deals) == 1

            # AND: 실패 로깅 확인
            mock_logger.error.assert_called()
