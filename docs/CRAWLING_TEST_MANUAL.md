# 크롤링 로컬 테스트 매뉴얼

> 새 크롤러 추가 또는 크롤링 로직 변경 시 반드시 실행

## 사전 조건

- Docker DB 컨테이너 실행 중 (`tuum-hotdeal-db`)
- Poetry 환경 설정 완료

## 1. DB 상태 확인

```bash
# 테이블 확인
docker exec tuum-hotdeal-db psql -U tuum -d tuum_hotdeal -c "\dt"

# 키워드 확인
docker exec tuum-hotdeal-db psql -U tuum -d tuum_hotdeal -c "SELECT * FROM hotdeal_keywords;"

# KeywordSite 확인
docker exec tuum-hotdeal-db psql -U tuum -d tuum_hotdeal -c "SELECT * FROM hotdeal_keyword_sites;"
```

## 2. 테스트 키워드 생성 (필요시)

```bash
docker exec tuum-hotdeal-db psql -U tuum -d tuum_hotdeal -c "
INSERT INTO hotdeal_keywords (title, wdate) VALUES 
('아이폰', NOW()),
('맥북', NOW()),
('에어팟', NOW())
ON CONFLICT (title) DO NOTHING;
"
```

## 3. 크롤링 테스트 스크립트 실행

```bash
cd /home/ubuntu/dev/tuum-hotdeal-fastapi

cat > test_crawl_local.py << 'EOF'
import asyncio
import httpx
from datetime import datetime
import os

os.environ['DATABASE_URL'] = 'postgresql://tuum:tuum1234@localhost:5433/tuum_hotdeal'
os.environ['ENVIRONMENT'] = 'local'
os.environ['DEBUG'] = 'false'
os.environ['PASSWORD_SECRET_KEY'] = 'test'
os.environ['EMAIL_SECRET_KEY'] = 'test'
os.environ['REFRESH_TOKEN_SECRET_KEY'] = 'test'

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.src.domain.hotdeal.enums import SiteName
from app.src.domain.hotdeal.models import Keyword, KeywordSite
from app.src.domain.mail.models import MailLog
from app.src.domain.user.models import User, user_keywords
from app.src.Infrastructure.crawling.crawlers import get_crawler, get_active_sites
from app.src.Infrastructure.crawling.proxy_manager import ProxyManager

ASYNC_DATABASE_URL = 'postgresql+asyncpg://tuum:tuum1234@localhost:5433/tuum_hotdeal'
async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
_unused = (User, user_keywords, MailLog)


async def test_crawl_and_save():
    print("=" * 60)
    print("크롤링 + DB 저장 테스트")
    print("=" * 60)
    
    print("\n[0] 프록시 수집 중...")
    proxy_manager = ProxyManager()
    proxy_manager.reset_proxies()
    proxies = proxy_manager.fetch_proxies()
    print(f"  수집된 프록시: {len(proxies)}개")
    
    active_sites = get_active_sites()
    print(f"\n[1] 활성 사이트: {[s.value for s in active_sites]}")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Keyword))
        keywords = result.scalars().all()
        print(f"[2] DB 키워드: {[k.title for k in keywords]}")
        
        if not keywords:
            print("키워드가 없습니다! 테스트 키워드를 먼저 생성하세요.")
            return
        
        test_keyword = keywords[0]
        print(f"\n[3] 테스트 키워드: '{test_keyword.title}' (id={test_keyword.id})")
        
        async with httpx.AsyncClient(timeout=30) as client:
            for site in active_sites:
                print(f"\n--- {site.value} 크롤링 ---")
                crawler = get_crawler(site, test_keyword.title, client)
                print(f"  검색 URL: {crawler.search_url}")
                
                try:
                    products = await crawler.fetchparse()
                    print(f"  크롤링 결과: {len(products)}건")
                    
                    if products:
                        p = products[0]
                        print(f"  첫 번째 상품:")
                        print(f"    - id: {p.id}")
                        print(f"    - title: {p.title[:50]}...")
                        print(f"    - price: {p.price}")
                        print(f"    - site_name: {p.site_name}")
                        print(f"    - search_url: {p.search_url}")
                        
                        stmt = select(KeywordSite).where(
                            KeywordSite.site_name == site,
                            KeywordSite.keyword_id == test_keyword.id,
                        )
                        existing = (await session.execute(stmt)).scalars().one_or_none()
                        
                        if existing:
                            existing.external_id = p.id
                            existing.link = p.link
                            existing.price = p.price
                            existing.wdate = datetime.now()
                            print(f"  DB 업데이트 완료")
                        else:
                            new_entry = KeywordSite(
                                keyword_id=test_keyword.id,
                                site_name=site,
                                external_id=p.id,
                                link=p.link,
                                price=p.price,
                                wdate=datetime.now(),
                            )
                            session.add(new_entry)
                            print(f"  DB 저장 완료")
                        
                        await session.commit()
                    else:
                        print(f"  크롤링 결과 없음")
                except Exception as e:
                    print(f"  오류: {e}")
    
    print("\n" + "=" * 60)
    print("[4] DB 저장 확인")
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(KeywordSite))
        sites = result.scalars().all()
        if sites:
            for s in sites:
                print(f"  - keyword_id={s.keyword_id}, site={s.site_name.value}, external_id={s.external_id[:30]}...")
        else:
            print("  저장된 데이터 없음")
    
    print("\n테스트 완료!")


if __name__ == "__main__":
    asyncio.run(test_crawl_and_save())
EOF

poetry run python test_crawl_local.py
```

## 4. 검증 항목

| 항목 | 확인 사항 |
|------|----------|
| 프록시 수집 | 프록시 리스트 수집 완료 |
| 403 우회 | 직접 요청 차단 시 프록시로 재시도 |
| 크롤링 결과 | 상품 목록 반환 (0건 이상) |
| 필수 필드 | `site_name`, `search_url` 값 정상 |
| DB 저장 | `hotdeal_keyword_sites` 테이블에 저장 |

## 5. 테스트 후 정리

```bash
# 테스트 스크립트 삭제
rm test_crawl_local.py

# 테스트 데이터 삭제 (선택)
docker exec tuum-hotdeal-db psql -U tuum -d tuum_hotdeal -c "
DELETE FROM hotdeal_keyword_sites;
DELETE FROM hotdeal_keywords;
"
```

## 6. 새 크롤러 추가 시 체크리스트

- [ ] `get_active_sites()`에 새 사이트 포함 확인
- [ ] `site_name` 필드가 올바른 `SiteName` enum 값 반환
- [ ] `search_url` 필드가 올바른 검색 URL 반환
- [ ] 프록시 우회 로직 정상 동작
- [ ] DB 저장 정상 동작
