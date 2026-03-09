# FUR-21 RCA: 최근 메일 미발송 문제

## 사건 요약

- 증상: 핫딜 알림 메일이 KST 2026-03-07 15:04 이후 발송되지 않음
- 조사 기준 이슈: `FUR-21`
- 조사 일시: 2026-03-09 (UTC)

## 타임라인 근거

- `db3c4f2` 배포 완료: `2026-03-07T05:30:35Z` (KST 2026-03-07 14:30:35)
- 워커 스케줄: `CronTrigger(minute="0,30")` (`app/worker_main.py`)
- 증상 관찰 시작: KST 2026-03-07 15:04

배포 직후 첫 정시 실행 구간(15:00 KST)부터 영향이 나타났을 가능성이 높다.

## 코드 레벨 재현 신호

### 1) 차단 응답 경로의 누적 대기

`app/src/Infrastructure/crawling/base_crawler.py`:

- 차단 응답(403/429/430) 시 `await asyncio.sleep(backoff_seconds)` 수행
- 이후 프록시 재시도 루프(`for _ in range(15)`)에서도 차단 응답마다 sleep 수행
- 백오프 예산(`CRAWL_BLOCK_BACKOFF_BUDGET_SECONDS`)을 초과할 때까지 누적 대기

기본 설정값 기준(`CRAWL_BLOCK_BACKOFF_SECONDS=3`, `MAX=60`, `BUDGET=180`)으로
키워드/사이트 1건당 누적 sleep이 `48초 ~ 180초`까지 커질 수 있다.

### 2) 워커 스케줄 스킵 조건

`app/worker_main.py`:

- `JOB_RUN_LOCK`이 잡혀 있으면 다음 실행을 건너뜀
- 스케줄은 30분 간격(`0,30`)

즉, 차단 응답이 누적되어 1회 실행 시간이 늘어나면 다음 스케줄 구간이 연속 스킵될 수 있다.

## Root Cause

차단 응답(429/403) 증가 상황에서 크롤링 단계의 누적 백오프 대기 시간이 길어지고,
워커의 단일 실행 락(`JOB_RUN_LOCK`)과 결합되면서 정기 실행이 실질적으로 지연/스킵되었다.
그 결과 핫딜 탐지/발송 사이클이 제때 완료되지 않아 메일 알림 공백이 발생했다.

## 영향 범위

- 핫딜 탐지 주기 지연 또는 스킵
- 메일 발송량 급감(또는 0건 구간 발생 가능)
- 워커는 실패로 종료되지 않아 외형상 정상처럼 보일 수 있음

## 후속 조치 이슈

- 생성 완료: `FUR-23` (Backlog)
- 제목: `차단 응답(429/403) 시 워커 장기 실행으로 인한 핫딜 알림 공백 방지`
- 관계: `FUR-23`는 `FUR-21`에 의해 block됨(`blockedBy` 의미)

## 검증에 사용한 명령

- `gh run list --workflow deploy.yml --limit 5 ...`
- `git show db3c4f2 -- app/src/Infrastructure/crawling/base_crawler.py app/worker_main.py`
- `DATABASE_URL=sqlite+aiosqlite:///:memory: ... poetry run pytest tests/infrastructure/test_base_crawler_browser.py -k '429 or cumulative_backoff'`
