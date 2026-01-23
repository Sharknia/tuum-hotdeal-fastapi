# 멀티사이트 크롤링 지원 계획

> 작성일: 2026-01-23
> 상태: 최종 확정 (구현 대기)
> 범위: 백엔드 + 프론트엔드 전체, 아키텍처 확장만 (새 크롤러 구현 제외)

## 개요

현재 알구몬(algumon.com) 단일 사이트만 지원하는 크롤링 엔진을 여러 핫딜 사이트(FM코리아, 뽐뿌 등)를 동시에 크롤링할 수 있도록 확장하는 계획.

---

## Phase 1: 스키마 및 크롤러 베이스 확장

> 목표: 멀티사이트를 위한 데이터 구조 정비

| 작업 | 파일 | 변경사항 |
|------|------|----------|
| 1-1 | `schemas.py` | `site_name: SiteName` 필수 필드 추가 |
| 1-2 | `schemas.py` | `search_url: str` 필드 추가 |
| 1-3 | `base_crawler.py` | `site_name` 추상 속성 추가 |
| 1-4 | `base_crawler.py` | `search_url` 속성 추가 (기본값 `self.url`) |
| 1-5 | `algumon.py` | `site_name` 구현 + `parse()`에서 설정 |
| 1-6 | `models.py` | `default=SiteName.ALGUMON` 제거 |

#### 수정된 CrawledKeyword
```python
class CrawledKeyword(BaseModel):
    id: str
    title: str
    link: str
    price: str | None = None
    meta_data: str | None = None
    site_name: SiteName  # Required!
    search_url: str      # Required!
```

#### 수정된 BaseCrawler
```python
class BaseCrawler(ABC):
    @property
    @abstractmethod
    def site_name(self) -> SiteName:
        """크롤러가 담당하는 사이트"""
        pass
    
    @property
    def search_url(self) -> str:
        """검색 결과 페이지 URL (기본값: self.url)"""
        return self.url
```

---

## Phase 2: 크롤러 레지스트리

> 목표: 사이트별 크롤러 동적 생성 지원

| 작업 | 파일 | 변경사항 |
|------|------|----------|
| 2-1 | `crawlers/__init__.py` | 레지스트리 + `get_crawler()` + `get_active_sites()` |

#### 레지스트리 구현
```python
# crawlers/__init__.py
from app.src.domain.hotdeal.enums import SiteName
from .base_crawler import BaseCrawler
from .crawlers.algumon import AlgumonCrawler

CRAWLER_REGISTRY: dict[SiteName, type[BaseCrawler]] = {
    SiteName.ALGUMON: AlgumonCrawler,
}

def get_crawler(site: SiteName, keyword: str, client) -> BaseCrawler:
    if site not in CRAWLER_REGISTRY:
        raise ValueError(f"Unsupported site: {site}")
    return CRAWLER_REGISTRY[site](keyword=keyword, client=client)

def get_active_sites() -> list[SiteName]:
    return list(CRAWLER_REGISTRY.keys())
```

---

## Phase 3: 워커 로직 수정

> 목표: 하드코딩 제거 및 멀티사이트 동시 크롤링 지원

| 작업 | 파일 | 변경사항 |
|------|------|----------|
| 3-1 | `worker_main.py` | import 변경 (레지스트리 사용) |
| 3-2 | `worker_main.py` | `job()` 내에서 사이트별 세마포어 생성 |
| 3-3 | `worker_main.py` | `get_new_hotdeal_keywords_for_site()` 함수 생성 |
| 3-4 | `worker_main.py` | `handle_keyword()` 멀티사이트 로직 |
| 3-5 | `worker_main.py` | DB 조회/저장 로직 파라미터화 |

#### 핵심 수정 사항

**1. 세마포어는 job() 내에서 생성**
```python
async def job():
    site_semaphores = {
        site: asyncio.Semaphore(2) for site in get_active_sites()
    }
    # ...
```

**2. handle_keyword 멀티사이트 로직**
```python
async def handle_keyword(
    keyword: Keyword, 
    client: httpx.AsyncClient,
    site_semaphores: dict[SiteName, asyncio.Semaphore]
) -> tuple[Keyword, list[CrawledKeyword]] | None:
    
    async def crawl_site(site: SiteName):
        async with site_semaphores[site]:
            await asyncio.sleep(random.uniform(1, 3))
            async with AsyncSessionLocal() as session:
                return await get_new_hotdeal_keywords_for_site(
                    session, keyword, client, site
                )
    
    site_results = await asyncio.gather(
        *[crawl_site(site) for site in get_active_sites()],
        return_exceptions=True
    )
    
    # 결과 병합 + 실패 로깅
    all_deals = []
    for i, res in enumerate(site_results):
        if isinstance(res, Exception):
            site = get_active_sites()[i]
            logger.error(f"[{keyword.title}] {site.value} 크롤링 실패: {res}")
        elif isinstance(res, list):
            all_deals.extend(res)
    
    return (keyword, all_deals) if all_deals else None
```

**3. get_new_hotdeal_keywords_for_site 함수**
```python
async def get_new_hotdeal_keywords_for_site(
    session: AsyncSession,
    keyword: Keyword,
    client: httpx.AsyncClient,
    site: SiteName,
) -> list[CrawledKeyword]:
    crawler = get_crawler(site, keyword.title, client)
    latest_products = await crawler.fetchparse()
    
    if not latest_products:
        return []
    
    stmt = select(KeywordSite).where(
        KeywordSite.site_name == site,
        KeywordSite.keyword_id == keyword.id,
    )
    # ... 이하 기존 로직 (site_name=site 로 변경)
```

---

## Phase 4: 메일 템플릿 수정

> 목표: 사이트별 그룹화된 이메일 생성

| 작업 | 파일 | 변경사항 |
|------|------|----------|
| 4-1 | `mail_manager.py` | 하드코딩 URL 제거 |
| 4-2 | `mail_manager.py` | 사이트별 그룹화 로직 추가 |

#### 수정된 템플릿 로직
```python
async def make_hotdeal_email_content(
    keyword: Keyword,
    updates: list[CrawledKeyword],
) -> str:
    from itertools import groupby
    
    if not updates:
        return ""
    
    sorted_updates = sorted(updates, key=lambda x: x.site_name.value)
    
    html = f"<h2>{keyword.title} 새 핫딜</h2>"
    
    for site_name, products in groupby(sorted_updates, key=lambda x: x.site_name):
        products_list = list(products)
        search_url = products_list[0].search_url
        site_display = site_name.value.upper()
        
        html += f"<h3><a href='{search_url}'>[{site_display}] 검색 결과</a></h3>"
        html += "".join([
            f"<p><a href='{p.link}'>{p.title}</a> - {p.price or '가격 미정'}</p>"
            for p in products_list
        ])
    
    return html
```

---

## Phase 5: 테스트 수정

> 목표: 변경된 시그니처 및 멀티사이트 로직 테스트

| 작업 | 파일 | 변경사항 |
|------|------|----------|
| 5-1 | `test_worker_main.py` | 테스트 데이터에 `site_name`, `search_url` 추가 |
| 5-2 | `test_worker_main.py` | fixture에서 `SiteName.ALGUMON` 명시적 전달 |
| 5-3 | `test_worker_main.py` | 모킹 방식 변경 (`get_crawler` 또는 레지스트리 패치) |
| 5-4 | `test_worker_main.py` | `get_new_hotdeal_keywords_for_site` 단위 테스트 |
| 5-5 | `test_worker_main.py` | 부분 실패 시나리오 테스트 |

---

## Phase 6: 프론트엔드 수정

> 목표: UI에서 멀티사이트 검색 링크 지원

| 작업 | 파일 | 변경사항 |
|------|------|----------|
| 6-1 | `keyword_manager.js` | 하드코딩된 알구몬 URL 제거 |
| 6-2 | `keyword_manager.js` | 사이트별 검색 링크 동적 생성 또는 대표 사이트 링크 유지 |

> 참고: 현재 키워드 API 응답에 사이트 정보가 없으므로, 프론트엔드에서는 기본 사이트(알구몬) 링크를 유지하거나 API 확장이 필요할 수 있음

---

## 구현 순서 요약

| Phase | 작업 | 복잡도 | 예상 소요 |
|:---:|------|:---:|:---:|
| 1 | 스키마/크롤러 베이스 확장 | 낮음 | 30분 |
| 2 | 크롤러 레지스트리 | 낮음 | 15분 |
| 3 | 워커 로직 수정 | 높음 | 1시간 |
| 4 | 메일 템플릿 수정 | 중간 | 30분 |
| 5 | 테스트 수정 | 중간 | 45분 |
| 6 | 프론트엔드 수정 | 낮음 | 15분 |

**총 예상 소요: 약 3시간**

---

## 해결된 기술적 이슈

1. **세마포어 이벤트 루프 바인딩** → `job()` 내 생성
2. **AsyncSession 동시 사용** → 사이트별 별도 session
3. **groupby None 처리** → `site_name` Required 필드화
4. **레지스트리 KeyError** → 명시적 ValueError 처리
5. **부분 실패 로깅** → 사이트별 에러 로깅 추가

---

## 향후 확장

새 사이트 추가 시 필요한 작업:
1. `crawlers/` 에 새 크롤러 클래스 생성 (예: `fmkorea.py`)
2. `CRAWLER_REGISTRY`에 등록
3. 끝! (워커, 메일, 프론트 수정 불필요)
