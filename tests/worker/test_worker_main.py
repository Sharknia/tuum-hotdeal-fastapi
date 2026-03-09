import asyncio
import signal
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import app.worker_main as worker_main_module
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.models import Keyword, KeywordSite
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.worker_main import (
    _apply_proxy_pool_protection,
    _resolve_crawl_concurrency,
    _resolve_timeout_seconds,
    get_new_hotdeal_keywords,
    get_new_hotdeal_keywords_for_site,
    handle_keyword,
    job,
    main,
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


def test_resolve_crawl_concurrency_uses_configured_defaults():
    with (
        patch.object(worker_main_module.settings, "CRAWL_SITE_CONCURRENCY", 2),
        patch.object(worker_main_module.settings, "CRAWL_KEYWORD_CONCURRENCY", 4),
        patch.object(worker_main_module.settings, "CRAWL_SITE_CONCURRENCY_MAX", 4),
        patch.object(worker_main_module.settings, "CRAWL_KEYWORD_CONCURRENCY_MAX", 8),
    ):
        site_limit, keyword_limit = _resolve_crawl_concurrency([SiteName.ALGUMON])

    assert site_limit == 2
    assert keyword_limit == 4


def test_resolve_crawl_concurrency_clamps_and_aligns_keyword_limit():
    with (
        patch.object(worker_main_module.settings, "CRAWL_SITE_CONCURRENCY", 10),
        patch.object(worker_main_module.settings, "CRAWL_KEYWORD_CONCURRENCY", 1),
        patch.object(worker_main_module.settings, "CRAWL_SITE_CONCURRENCY_MAX", 4),
        patch.object(worker_main_module.settings, "CRAWL_KEYWORD_CONCURRENCY_MAX", 8),
    ):
        site_limit, keyword_limit = _resolve_crawl_concurrency([SiteName.ALGUMON])

    assert site_limit == 4
    assert keyword_limit == 4


def test_apply_proxy_pool_protection_reduces_limits_and_prioritizes_keywords():
    keywords = [
        Mock(title="beta", users=[1]),
        Mock(title="alpha", users=[1, 2, 3]),
        Mock(title="gamma", users=[1, 2]),
        Mock(title="delta", users=[1]),
    ]

    with (
        patch.object(worker_main_module.settings, "CRAWL_PROTECTION_SITE_CONCURRENCY", 1),
        patch.object(worker_main_module.settings, "CRAWL_PROTECTION_KEYWORD_CONCURRENCY", 2),
        patch.object(worker_main_module.settings, "CRAWL_PROTECTION_KEYWORD_RATIO", 0.5),
    ):
        selected, protected_site_limit, protected_keyword_limit = _apply_proxy_pool_protection(
            keywords,
            site_limit=4,
            keyword_limit=6,
        )

    assert protected_site_limit == 1
    assert protected_keyword_limit == 2
    assert [keyword.title for keyword in selected] == ["alpha", "gamma"]


@pytest.mark.parametrize(
    ("configured", "fallback", "expected"),
    [
        (30.0, 10.0, 30.0),
        ("45", 10.0, 45.0),
        (0, 10.0, 10.0),
        (-1, 10.0, 10.0),
        ("invalid", 10.0, 10.0),
    ],
)
def test_resolve_timeout_seconds(configured, fallback, expected):
    resolved = _resolve_timeout_seconds("TEST_TIMEOUT", configured, fallback)
    assert resolved == expected


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
            assert saved_site.external_id == "101,102,103"


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
            assert old_site_data.external_id == "101,102,103"


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
            assert saved_site.external_id == "101,102,103"


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
            assert old_site_data.external_id == "101,102,103"


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


@pytest.mark.asyncio
async def test_handle_keyword_multisite_timeout_keeps_partial_success(
    mock_db_session: AsyncSession, keyword_in_db: Keyword
):
    """
    시나리오: 일부 사이트가 시간 제한을 초과
    - 기대: 제한 초과 사이트는 건너뛰고 성공 사이트 결과를 유지
    """
    site_semaphores = {SiteName.ALGUMON: asyncio.Semaphore(2)}
    call_count = 0

    async def mock_get_for_site_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return CRAWLED_DATA_NEW[:1]

        await asyncio.sleep(0.05)
        return CRAWLED_DATA_NEW[:1]

    with (
        patch(
            "app.worker_main.get_active_sites",
            return_value=[SiteName.ALGUMON, SiteName.ALGUMON],
        ),
        patch.object(worker_main_module.settings, "CRAWL_SITE_BUDGET_SECONDS", 0.01),
        patch(
            "app.worker_main.get_new_hotdeal_keywords_for_site", new_callable=AsyncMock
        ) as mock_get_for_site,
        patch("app.worker_main.AsyncSessionLocal", return_value=mock_db_session),
        patch("app.worker_main.logger") as mock_logger,
    ):
        mock_get_for_site.side_effect = mock_get_for_site_side_effect

        async with httpx.AsyncClient() as client:
            result = await handle_keyword(keyword_in_db, client, site_semaphores)

    assert result is not None
    _, deals = result
    assert len(deals) == 1
    mock_logger.warning.assert_called()


@pytest.mark.asyncio
async def test_graceful_shutdown_signal():
    """SIGTERM/SIGINT 시 graceful shutdown 경로가 실행되어야 한다."""

    class DummyScheduler:
        def __init__(self):
            self.shutdown_calls: list[bool] = []

        def add_job(self, *_args, **_kwargs):
            return None

        def start(self):
            return None

        def shutdown(self, wait: bool = True):
            self.shutdown_calls.append(wait)

    scheduler = DummyScheduler()
    handlers: dict[signal.Signals, callable] = {}
    handlers_ready = asyncio.Event()

    class DummyLoop:
        def add_signal_handler(self, sig, callback, *args):
            handlers[sig] = lambda: callback(*args)
            if len(handlers) == 2:
                handlers_ready.set()

    mock_browser = AsyncMock()
    mock_engine_dispose = AsyncMock()
    mock_engine = type("DummyEngine", (), {"dispose": mock_engine_dispose})()

    with (
        patch("app.worker_main.AsyncIOScheduler", return_value=scheduler),
        patch("app.worker_main.asyncio.get_running_loop", return_value=DummyLoop()),
        patch("app.worker_main.SharedBrowser") as mock_shared_browser,
        patch("app.worker_main.async_engine", new=mock_engine),
    ):
        mock_shared_browser.get_instance.return_value.stop = mock_browser

        main_task = asyncio.create_task(main())
        await asyncio.wait_for(handlers_ready.wait(), timeout=1)

        handlers[signal.SIGTERM]()
        await asyncio.wait_for(main_task, timeout=2)

    assert scheduler.shutdown_calls == [False]
    mock_browser.assert_awaited_once()
    mock_engine_dispose.assert_awaited_once()


@pytest.mark.asyncio
async def test_shutdown_calls_browser_stop_and_engine_dispose():
    """종료 순서: scheduler shutdown -> in-flight 대기 -> browser stop -> engine dispose."""

    order: list[str] = []
    handlers: dict[signal.Signals, callable] = {}
    handlers_ready = asyncio.Event()
    job_started = asyncio.Event()
    release_job = asyncio.Event()
    job_finished = asyncio.Event()

    async def mock_job():
        job_started.set()
        await release_job.wait()
        order.append("job_finished")
        job_finished.set()

    class DummyScheduler:
        def __init__(self):
            self.job_func = None

        def add_job(self, func, *_args, **_kwargs):
            self.job_func = func

        def start(self):
            return None

        def shutdown(self, wait: bool = True):
            order.append("scheduler_shutdown")
            assert wait is False
            release_job.set()

    scheduler = DummyScheduler()

    class DummyLoop:
        def add_signal_handler(self, sig, callback, *args):
            handlers[sig] = lambda: callback(*args)
            if len(handlers) == 2:
                handlers_ready.set()

    async def mock_browser_stop():
        assert job_finished.is_set()
        order.append("browser_stop")

    async def mock_engine_dispose(_self):
        order.append("engine_dispose")

    mock_engine = type("DummyEngine", (), {"dispose": mock_engine_dispose})()

    with (
        patch("app.worker_main.AsyncIOScheduler", return_value=scheduler),
        patch("app.worker_main.asyncio.get_running_loop", return_value=DummyLoop()),
        patch("app.worker_main.job", new=mock_job),
        patch("app.worker_main.SharedBrowser") as mock_shared_browser,
        patch("app.worker_main.async_engine", new=mock_engine),
    ):
        mock_shared_browser.get_instance.return_value.stop = AsyncMock(
            side_effect=mock_browser_stop
        )

        main_task = asyncio.create_task(main())
        await asyncio.wait_for(handlers_ready.wait(), timeout=1)

        assert scheduler.job_func is not None
        in_flight_task = asyncio.create_task(scheduler.job_func())
        await asyncio.wait_for(job_started.wait(), timeout=1)

        handlers[signal.SIGINT]()
        await asyncio.wait_for(main_task, timeout=2)
        await asyncio.wait_for(in_flight_task, timeout=1)

    assert order == [
        "scheduler_shutdown",
        "job_finished",
        "browser_stop",
        "engine_dispose",
    ]


@pytest.mark.asyncio
async def test_scheduler_single_instance():
    """스케줄러 등록 옵션이 단일 실행 정책으로 고정되어야 한다."""

    class DummyScheduler:
        def __init__(self):
            self.add_job_kwargs = None

        def add_job(self, _func, *_args, **kwargs):
            self.add_job_kwargs = kwargs

        def start(self):
            return None

        def shutdown(self, wait: bool = True):
            return None

    scheduler = DummyScheduler()
    handlers: dict[signal.Signals, callable] = {}
    handlers_ready = asyncio.Event()

    class DummyLoop:
        def add_signal_handler(self, sig, callback, *args):
            handlers[sig] = lambda: callback(*args)
            if len(handlers) == 2:
                handlers_ready.set()

    mock_browser = AsyncMock()
    mock_engine_dispose = AsyncMock()
    mock_engine = type("DummyEngine", (), {"dispose": mock_engine_dispose})()

    with (
        patch("app.worker_main.AsyncIOScheduler", return_value=scheduler),
        patch("app.worker_main.asyncio.get_running_loop", return_value=DummyLoop()),
        patch("app.worker_main.SharedBrowser") as mock_shared_browser,
        patch("app.worker_main.async_engine", new=mock_engine),
    ):
        mock_shared_browser.get_instance.return_value.stop = mock_browser

        main_task = asyncio.create_task(main())
        await asyncio.wait_for(handlers_ready.wait(), timeout=1)
        handlers[signal.SIGTERM]()
        await asyncio.wait_for(main_task, timeout=2)

    assert scheduler.add_job_kwargs is not None
    assert scheduler.add_job_kwargs["max_instances"] == 1
    assert scheduler.add_job_kwargs["coalesce"] is True
    assert scheduler.add_job_kwargs["misfire_grace_time"] == 300


@pytest.mark.asyncio
async def test_job_lock_prevents_overlap():
    """동시 트리거 시 job 본문은 1회만 실행되어야 한다."""

    run_started = asyncio.Event()
    release_run = asyncio.Event()

    async def mock_run_job_once():
        run_started.set()
        await release_run.wait()

    with (
        patch("app.worker_main.JOB_RUN_LOCK", new=asyncio.Lock()),
        patch("app.worker_main._run_job_once", new=AsyncMock(side_effect=mock_run_job_once)) as mock_run,
    ):
        first_task = asyncio.create_task(job())
        await asyncio.wait_for(run_started.wait(), timeout=1)

        second_task = asyncio.create_task(job())
        await asyncio.sleep(0)

        release_run.set()
        await asyncio.gather(first_task, second_task)

    assert mock_run.await_count == 1


@pytest.mark.asyncio
async def test_job_timeout_releases_lock_and_allows_next_run():
    """timeout 이후에도 락이 해제되어 다음 실행이 정상 시작되어야 한다."""

    call_count = 0

    async def mock_run_job_once():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            await asyncio.sleep(0.05)

    with (
        patch("app.worker_main.JOB_RUN_LOCK", new=asyncio.Lock()),
        patch.object(worker_main_module.settings, "WORKER_RUN_TIMEOUT_SECONDS", 0.01),
        patch(
            "app.worker_main._run_job_once",
            new=AsyncMock(side_effect=mock_run_job_once),
        ) as mock_run,
    ):
        await job()
        await job()

    assert mock_run.await_count == 2


@pytest.mark.asyncio
async def test_job_cancelled_error_cleanup_order():
    """취소 발생 시 상태 업데이트 후 browser stop이 호출되어야 한다."""

    order: list[str] = []

    created_log = worker_main_module.WorkerLog(status=worker_main_module.WorkerStatus.RUNNING)
    created_log.id = 101

    create_session = AsyncMock()
    create_session.add = Mock()
    create_session.commit = AsyncMock()

    async def create_refresh(entry):
        entry.id = created_log.id

    create_session.refresh = AsyncMock(side_effect=create_refresh)

    create_session_cm = AsyncMock()
    create_session_cm.__aenter__.return_value = create_session
    create_session_cm.__aexit__.return_value = None

    updated_log = Mock()
    updated_log.status = worker_main_module.WorkerStatus.RUNNING
    updated_log.message = None
    updated_log.details = None

    update_result = Mock()
    update_result.scalars.return_value.first.return_value = updated_log

    update_session = AsyncMock()
    update_session.execute = AsyncMock(return_value=update_result)

    async def update_commit():
        order.append("status_update")

    update_session.commit = AsyncMock(side_effect=update_commit)

    update_session_cm = AsyncMock()
    update_session_cm.__aenter__.return_value = update_session
    update_session_cm.__aexit__.return_value = None

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(side_effect=asyncio.CancelledError())

    mock_http_client_cm = AsyncMock()
    mock_http_client_cm.__aenter__.return_value = mock_http_client
    mock_http_client_cm.__aexit__.return_value = None

    mock_browser_start = AsyncMock()

    async def browser_stop():
        order.append("browser_stop")

    mock_browser_stop = AsyncMock(side_effect=browser_stop)

    with (
        patch("app.worker_main.AsyncSessionLocal", side_effect=[create_session_cm, update_session_cm]),
        patch("app.worker_main.get_active_sites", return_value=[SiteName.ALGUMON]),
        patch("app.worker_main._requires_browser", new=AsyncMock(return_value=True)),
        patch("app.worker_main.httpx.AsyncClient", return_value=mock_http_client_cm),
        patch("app.worker_main.SharedBrowser") as mock_shared_browser,
    ):
        mock_shared_browser.get_instance.return_value.start = mock_browser_start
        mock_shared_browser.get_instance.return_value.stop = mock_browser_stop

        with pytest.raises(asyncio.CancelledError):
            await worker_main_module._run_job_once()

    assert updated_log.status == worker_main_module.WorkerStatus.FAIL
    assert updated_log.message == "Job cancelled"
    assert order == ["status_update", "browser_stop"]


@pytest.mark.asyncio
async def test_job_logs_defunct_warning_when_nonzero():
    """job 종료 시 defunct count가 0보다 크면 warning을 남겨야 한다."""

    with (
        patch("app.worker_main.JOB_RUN_LOCK", new=asyncio.Lock()),
        patch("app.worker_main._run_job_once", new=AsyncMock()),
        patch("app.worker_main._probe_defunct_count", return_value=3),
        patch("app.worker_main._log_process_identity"),
        patch("app.worker_main.logger") as mock_logger,
    ):
        await job()

    mock_logger.warning.assert_called_once_with(
        "[WARN] job 종료 시 defunct 프로세스 감지: %s", 3
    )


@pytest.mark.asyncio
async def test_job_skips_browser_when_not_required():
    """활성 크롤러가 브라우저를 요구하지 않으면 start/stop을 호출하지 않아야 한다."""

    mock_response = Mock(status_code=200)
    mock_response.raise_for_status = Mock()

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)

    mock_http_client_cm = AsyncMock()
    mock_http_client_cm.__aenter__.return_value = mock_http_client
    mock_http_client_cm.__aexit__.return_value = None

    mock_scalars = Mock()
    mock_scalars.unique.return_value.all.return_value = []
    mock_result = Mock()
    mock_result.scalars.return_value = mock_scalars

    mock_session = AsyncMock()
    mock_session.add = Mock()
    mock_session.execute = AsyncMock(side_effect=[mock_result, mock_result])
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__.return_value = mock_session
    mock_session_cm.__aexit__.return_value = None

    mock_browser_start = AsyncMock()
    mock_browser_stop = AsyncMock()

    with (
        patch("app.worker_main.JOB_RUN_LOCK", new=asyncio.Lock()),
        patch("app.worker_main.httpx.AsyncClient", return_value=mock_http_client_cm),
        patch("app.worker_main.AsyncSessionLocal", return_value=mock_session_cm),
        patch("app.worker_main.get_active_sites", return_value=[SiteName.ALGUMON]),
        patch(
            "app.worker_main.get_crawler",
            return_value=Mock(requires_browser=False),
        ),
        patch("app.worker_main.SharedBrowser") as mock_shared_browser,
    ):
        mock_shared_browser.get_instance.return_value.start = mock_browser_start
        mock_shared_browser.get_instance.return_value.stop = mock_browser_stop

        await job()

    assert mock_shared_browser.get_instance.return_value.start.await_count == 0
    assert mock_shared_browser.get_instance.return_value.stop.await_count == 0


@pytest.mark.asyncio
async def test_job_starts_browser_when_required():
    """활성 크롤러 중 하나라도 브라우저를 요구하면 start/stop을 1회씩 호출해야 한다."""

    mock_response = Mock(status_code=200)
    mock_response.raise_for_status = Mock()

    mock_http_client = AsyncMock()
    mock_http_client.get = AsyncMock(return_value=mock_response)

    mock_http_client_cm = AsyncMock()
    mock_http_client_cm.__aenter__.return_value = mock_http_client
    mock_http_client_cm.__aexit__.return_value = None

    mock_scalars = Mock()
    mock_scalars.unique.return_value.all.return_value = []
    mock_result = Mock()
    mock_result.scalars.return_value = mock_scalars

    mock_session = AsyncMock()
    mock_session.add = Mock()
    mock_session.execute = AsyncMock(side_effect=[mock_result, mock_result])
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    mock_session_cm = AsyncMock()
    mock_session_cm.__aenter__.return_value = mock_session
    mock_session_cm.__aexit__.return_value = None

    mock_browser_start = AsyncMock()
    mock_browser_stop = AsyncMock()

    with (
        patch("app.worker_main.JOB_RUN_LOCK", new=asyncio.Lock()),
        patch("app.worker_main.httpx.AsyncClient", return_value=mock_http_client_cm),
        patch("app.worker_main.AsyncSessionLocal", return_value=mock_session_cm),
        patch("app.worker_main.get_active_sites", return_value=[SiteName.ALGUMON]),
        patch(
            "app.worker_main.get_crawler",
            return_value=Mock(requires_browser=True),
        ),
        patch("app.worker_main.SharedBrowser") as mock_shared_browser,
    ):
        mock_shared_browser.get_instance.return_value.start = mock_browser_start
        mock_shared_browser.get_instance.return_value.stop = mock_browser_stop

        await job()

    assert mock_shared_browser.get_instance.return_value.start.await_count == 1
    assert mock_shared_browser.get_instance.return_value.stop.await_count == 1


@pytest.mark.asyncio
async def test_process_identity_logging():
    """worker/job 시작/종료 시 진단 payload가 구조화되어 기록되어야 한다."""

    class DummyScheduler:
        def add_job(self, *_args, **_kwargs):
            return None

        def start(self):
            return None

        def shutdown(self, wait: bool = True):
            return None

    scheduler = DummyScheduler()
    handlers: dict[signal.Signals, callable] = {}
    handlers_ready = asyncio.Event()

    class DummyLoop:
        def add_signal_handler(self, sig, callback, *args):
            handlers[sig] = lambda: callback(*args)
            if len(handlers) == 2:
                handlers_ready.set()

    def fake_collect(event: str):
        return {
            "event": event,
            "pid": 123,
            "ppid": 1,
            "command": "python -m app.worker_main",
            "ppid_command": "tini",
            "cgroup": "0::/docker/demo",
            "defunct_count": 0,
        }

    mock_engine_dispose = AsyncMock()
    mock_engine = type("DummyEngine", (), {"dispose": mock_engine_dispose})()

    with (
        patch("app.worker_main._collect_process_identity", side_effect=fake_collect),
        patch("app.worker_main.logger") as mock_logger,
        patch("app.worker_main.AsyncIOScheduler", return_value=scheduler),
        patch("app.worker_main.asyncio.get_running_loop", return_value=DummyLoop()),
        patch("app.worker_main.SharedBrowser") as mock_shared_browser,
        patch("app.worker_main.async_engine", new=mock_engine),
        patch("app.worker_main.JOB_RUN_LOCK", new=asyncio.Lock()),
        patch("app.worker_main._run_job_once", new=AsyncMock()),
    ):
        mock_shared_browser.get_instance.return_value.stop = AsyncMock()

        main_task = asyncio.create_task(main())
        await asyncio.wait_for(handlers_ready.wait(), timeout=1)
        handlers[signal.SIGTERM]()
        await asyncio.wait_for(main_task, timeout=2)

        await job()

    diag_calls = [
        call
        for call in mock_logger.info.call_args_list
        if call.args and call.args[0] == "[DIAG] process_identity %s"
    ]
    payloads = [call.args[1] for call in diag_calls]

    assert {payload["event"] for payload in payloads} >= {
        "worker_start",
        "worker_end",
        "job_start",
        "job_end",
    }

    for payload in payloads:
        assert payload["pid"] == 123
        assert payload["ppid"] == 1
        assert payload["command"] == "python -m app.worker_main"
        assert payload["cgroup"] == "0::/docker/demo"
        assert payload["defunct_count"] == 0


def test_defunct_count_probe_fallback():
    """/proc 접근 실패 시 defunct_count probe는 -1을 반환해야 한다."""

    with patch("app.worker_main.Path.iterdir", side_effect=OSError("proc unavailable")):
        assert worker_main_module._probe_defunct_count() == -1
