import asyncio
import random
from datetime import datetime

import httpx
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import Result, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.src.core.config import settings
from app.src.core.logger import logger
from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.models import Keyword, KeywordSite
from app.src.domain.hotdeal.schemas import CrawledKeyword
from app.src.domain.mail.models import MailLog
from app.src.domain.user.models import User, user_keywords

# 프로젝트의 공통 설정과 DB 세션을 가져옵니다
from app.src.Infrastructure.crawling.crawlers import get_active_sites, get_crawler
from app.src.Infrastructure.crawling.proxy_manager import ProxyManager
from app.src.Infrastructure.mail.mail_manager import (
    make_hotdeal_email_content,
    send_email,
)

# User 모델을 사용하므로 _unused 튜플에서 제거하거나 주석 처리합니다.
_unused = (user_keywords, MailLog)

ASYNC_DATABASE_URL = settings.DATABASE_URL.replace(
    "postgresql://", "postgresql+asyncpg://", 1
)
if settings.ENVIRONMENT != "prod":
    ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("db", "localhost", 1).replace(
        "5432", "5433"
    )

async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_recycle=3600,
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)


PROXY_MANAGER = ProxyManager()


async def handle_keyword(
    keyword: Keyword,
    client: httpx.AsyncClient,
    site_semaphores: dict[SiteName, asyncio.Semaphore],
) -> tuple[Keyword, list[CrawledKeyword]] | None:
    """
    단일 키워드를 모든 활성 사이트에서 크롤링하고, 신규 핫딜이 있는 경우 결과를 반환합니다.
    """
    logger.info(f"[INFO] 키워드 처리: [{keyword.title}]")

    # 활성 사이트 목록을 한 번만 조회 (일관성 보장)
    active_sites = get_active_sites()

    async def crawl_site(site: SiteName) -> list[CrawledKeyword]:
        """특정 사이트에서 크롤링 수행 (세마포어로 동시성 제어)"""
        async with site_semaphores[site]:
            # 각 작업 사이에 랜덤한 지연을 주어 서버 부하를 분산
            await asyncio.sleep(random.uniform(1, 3))
            async with AsyncSessionLocal() as session:
                return await get_new_hotdeal_keywords_for_site(
                    session, keyword, client, site
                )

    # 모든 활성 사이트에서 병렬 크롤링
    site_results = await asyncio.gather(
        *[crawl_site(site) for site in active_sites],
        return_exceptions=True,
    )

    # 결과 병합 + 실패 로깅
    all_deals: list[CrawledKeyword] = []
    for i, res in enumerate(site_results):
        if isinstance(res, Exception):
            site = active_sites[i]
            logger.error(f"[{keyword.title}] {site.value} 크롤링 실패: {res}")
        elif isinstance(res, list):
            all_deals.extend(res)

    if all_deals:
        logger.info(
            f"[INFO] 키워드 처리: [{keyword.title}] 신규 핫딜 {len(all_deals)}건 발견"
        )
        return keyword, all_deals
    else:
        logger.info(f"[INFO] 키워드 처리: [{keyword.title}] 크롤링 결과 없음")
        return None


async def get_new_hotdeal_keywords_for_site(
    session: AsyncSession,
    keyword: Keyword,
    client: httpx.AsyncClient,
    site: SiteName,
) -> list[CrawledKeyword]:
    """
    특정 사이트에서 새로운 핫딜 키워드를 조회합니다.
    1. 해당 키워드로 크롤링을 수행하여 최신 핫딜 목록을 가져옵니다.
    2. DB에서 이전에 저장된 KeywordSite 정보를 조회하여 마지막으로 확인한 핫딜을 찾습니다.
    3. 최신 핫딜 목록과 마지막 확인 핫딜을 비교하여 새로운 핫딜만 필터링합니다.
    4. 새로운 핫딜이 있는 경우, KeywordSite 정보를 최신 핫딜로 업데이트하고 새로운 핫딜 목록을 반환합니다.
    5. 새로운 핫딜이 없는 경우, 빈 목록을 반환합니다.
    """
    # 1. 크롤링으로 최신 핫딜 목록 가져오기
    crawler = get_crawler(site, keyword.title, client)
    latest_products: list[CrawledKeyword] = await crawler.fetchparse()

    if not latest_products:
        return []

    # 2. DB에서 이전에 저장된 KeywordSite 정보 조회
    stmt = select(KeywordSite).where(
        KeywordSite.site_name == site,
        KeywordSite.keyword_id == keyword.id,
    )
    result: Result = await session.execute(stmt)
    last_crawled_site: KeywordSite | None = result.scalars().one_or_none()

    # 3. 새로운 핫딜 필터링
    new_deals: list[CrawledKeyword] = []
    if not last_crawled_site:
        # 첫 크롤링인 경우, 최신 1개만 새로운 핫딜로 간주
        new_deals = latest_products[:1]
    else:
        # 마지막으로 크롤링된 핫딜의 인덱스를 찾음
        try:
            last_crawled_index = [p.id for p in latest_products].index(
                last_crawled_site.external_id
            )
            new_deals = latest_products[:last_crawled_index]
        except ValueError:
            # 마지막으로 크롤링된 핫딜이 목록에 없으면 전부 새로운 핫딜로 간주
            new_deals = latest_products

    # 4. 새로운 핫딜이 있으면 DB 업데이트 및 반환
    if new_deals:
        newest_product = new_deals[0]
        if last_crawled_site:
            # 기존 정보 업데이트
            last_crawled_site.external_id = newest_product.id
            last_crawled_site.link = newest_product.link
            last_crawled_site.price = newest_product.price
            last_crawled_site.meta_data = newest_product.meta_data
            last_crawled_site.wdate = datetime.now()
        else:
            # 첫 크롤링 정보 저장
            new_site_entry = KeywordSite(
                keyword_id=keyword.id,
                site_name=site,
                external_id=newest_product.id,
                link=newest_product.link,
                price=newest_product.price,
                meta_data=newest_product.meta_data,
            )
            session.add(new_site_entry)

        await session.commit()
        return new_deals

    # 5. 새로운 핫딜이 없으면 빈 목록 반환
    return []


async def get_new_hotdeal_keywords(
    session: AsyncSession,
    keyword: Keyword,
    client: httpx.AsyncClient,
) -> list[CrawledKeyword]:
    """
    새로운 핫딜 키워드를 조회합니다. (하위 호환성 유지)
    내부적으로 get_new_hotdeal_keywords_for_site()를 호출합니다.
    """
    return await get_new_hotdeal_keywords_for_site(
        session, keyword, client, SiteName.ALGUMON
    )


async def job():
    """
    사용자와 연결된 키워드만 불러와 병렬로 처리하고, 결과를 취합하여 메일을 발송합니다.
    """

    # Supabase DB 활성화를 위한 주기적인 호출
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://aijlptoknzteaplgkemr.supabase.co/storage/v1/object/public/common//tuum.ico",
                timeout=10,
            )
            response.raise_for_status()  # HTTP 4xx/5xx 에러 발생 시 예외 처리
            logger.info(f"Supabase keep-alive call successful: {response.status_code}")
    except httpx.RequestError as e:
        logger.error(f"Supabase keep-alive call failed due to request error: {e}")
    except httpx.HTTPStatusError as e:
        logger.error(
            f"Supabase keep-alive call failed due to HTTP error: {e.response.status_code} - {e.response.text}"
        )
    except Exception as e:
        logger.error(f"Supabase keep-alive call failed: {e}")

    keywords_to_process: list[Keyword] = []
    all_users_with_keywords: list[User] = []  # 사용자 정보를 담을 리스트 추가

    try:
        async with AsyncSessionLocal() as session:
            # 사용자와 매핑된 키워드만 조회
            stmt = select(Keyword).where(Keyword.users.any())
            result = await session.execute(stmt)
            keywords_to_process = result.scalars().unique().all()

            # 메일 발송을 위해 모든 사용자 정보 미리 로드 (키워드 정보 포함)
            user_stmt = select(User).options(selectinload(User.keywords))
            user_result = await session.execute(user_stmt)
            all_users_with_keywords = user_result.scalars().unique().all()
    except Exception as e:
        logger.error(f"DB 조회 중 오류 발생: {e}")
        return  # DB 조회 실패 시 작업 중단

    if not keywords_to_process:
        logger.info("[INFO] 처리할 활성 키워드가 없습니다.")
        return

    PROXY_MANAGER.reset_proxies()
    PROXY_MANAGER.fetch_proxies()

    id_to_crawled_keyword: dict[Keyword, list[CrawledKeyword]] = {}

    # 사이트별 동시 실행 개수를 2개로 제한하는 세마포어 생성
    site_semaphores = {site: asyncio.Semaphore(2) for site in get_active_sites()}
    # 키워드별 동시 실행 개수를 5개로 제한하는 세마포어
    keyword_semaphore = asyncio.Semaphore(5)

    async with httpx.AsyncClient() as client:
        # 각 키워드를 세마포어 제어 하에 처리하는 태스크 리스트 생성
        async def sem_handle_keyword(keyword: Keyword):
            async with keyword_semaphore:
                # 세마포어 내에서도 짧은 랜덤 딜레이를 주면 부하를 더 분산시킬 수 있습니다.
                await asyncio.sleep(random.uniform(0.5, 1.5))
                return await handle_keyword(keyword, client, site_semaphores)

        tasks = [sem_handle_keyword(kw) for kw in keywords_to_process]

        # asyncio.gather로 모든 작업을 동시에 실행 (세마포어가 동시성 제어)
        # return_exceptions=True를 통해 일부 작업이 실패해도 전체가 중단되지 않도록 함
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # 결과 처리
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            # 실패한 경우, 어떤 키워드에서 오류가 났는지 로깅
            failed_keyword = keywords_to_process[i]
            logger.error(f"키워드 '[{failed_keyword.title}]' 처리 중 오류 발생: {res}")
        elif res:
            keyword, deals = res
            id_to_crawled_keyword[keyword] = deals

    logger.info("[INFO] 모든 키워드 크롤링 완료. 메일 발송 시작...")

    # 사용자별 메일 발송 로직
    email_tasks = []
    for user in all_users_with_keywords:
        try:
            user_deals: dict[Keyword, list[CrawledKeyword]] = {}
            # 사용자가 구독한 Keyword 객체들을 set으로 만들어 빠른 조회를 지원
            subscribed_keywords_set = set(user.keywords)

            # 사용자가 구독한 키워드 중 크롤링된 결과가 있는지 확인
            for crawled_keyword_obj, deals in id_to_crawled_keyword.items():
                if crawled_keyword_obj in subscribed_keywords_set:
                    user_deals[crawled_keyword_obj] = deals

            if user_deals:
                # 메일 내용 생성
                email_content: str = ""
                subject: str = ""
                for keyword, deals in user_deals.items():
                    try:
                        email_content += await make_hotdeal_email_content(
                            keyword, deals
                        )
                        subject += f"{keyword.title}, "
                    except Exception as e:
                        logger.error(
                            f"사용자 {user.email}, 키워드 {keyword.title} 메일 내용 생성 중 오류: {e}"
                        )
                        # 내용 생성 실패 시 해당 키워드는 건너뛰고 계속 진행
                        continue

                if not email_content:
                    # 모든 키워드에서 내용 생성 실패 시 메일 발송 안함
                    logger.info(
                        f"[INFO] 사용자 {user.email} 에게 발송할 유효한 메일 내용 없음"
                    )
                    continue

                subject = subject.rstrip(", ")  # 마지막 쉼표 및 공백 제거
                subject = f"[{subject}] 새로운 핫딜 알림"

                if settings.ENVIRONMENT == "prod":
                    task = send_email(
                        subject=subject,
                        to=user.email,
                        body=email_content,
                        is_html=True,
                    )
                    email_tasks.append(task)
                    # 메일 발송 성공 로그 (선택적)
                    # logger.info(f"사용자 {user.email} 에게 메일 발송 완료.")
                else:
                    logger.info(
                        f"[DEV] 사용자 {user.email} 에게 메일 발송 제목:{subject} 내용:{email_content}"
                    )
            # else:
            # 발송할 딜 없는 경우 로그는 위에서 처리했으므로 주석처리 또는 제거
            # print(f"[INFO] 사용자 {user.email} 에게 발송할 새 핫딜 없음")
        except Exception as e:
            # 사용자별 메일 처리 루프 전체에서 예외 발생 시 로깅
            logger.error(f"사용자 {user.email} 메일 처리 중 오류 발생: {e}")
            # 다음 사용자로 계속 진행
            continue

    if email_tasks:
        await asyncio.gather(*email_tasks)

    # 작업이 완료되면 지역 변수인 id_to_crawled_keyword는 자동으로 사라집니다.
    logger.info("[INFO] 메일 발송 완료 및 크롤링 결과 초기화")


async def main():
    scheduler = AsyncIOScheduler(timezone="Asia/Seoul")

    trigger = CronTrigger(minute="0,30")
    if settings.ENVIRONMENT != "prod":
        trigger = CronTrigger(minute="*")

    scheduler.add_job(
        job,
        trigger=trigger,
        id="hotdeal_worker",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "[INFO] Worker 스케줄러 시작: 매시 정각 및 30분마다 크롤링 및 메일 발송"
    )

    try:
        # 스케줄러가 백그라운드에서 실행되는 동안 메인 코루틴을 유지합니다.
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        logger.info("[INFO] Worker 종료 중...")
        scheduler.shutdown()


if __name__ == "__main__":
    if settings.ENVIRONMENT == "prod":
        asyncio.run(main())
    else:
        asyncio.run(job())
