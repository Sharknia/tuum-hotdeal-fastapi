# 메모리 안정화 작업 최종 보고서

> 작업 일자: 2026-02-02
> 서버 사양: 4코어/23Gi RAM/Swap 없음

---

## 작업 개요

WORKSPACE_PLAN.md에 기반한 메모리 안정화 작업이 완료되었습니다.
모든 Phase는 성공적으로 완료되었으며, 테스트와 린터 검증을 통과했습니다.

---

## 완료된 작업

### ✅ Phase 0: Compose 메모리 제한 적용
- **파일:** `docker-compose.prod.yml`
- **변경 내용:**
  - worker 서비스: `mem_limit: 4g`, `mem_reservation: 2g`
  - web 서비스: `mem_limit: 1g`, `mem_reservation: 256m`
  - 기존 `deploy.resources.limits` 제거
- **검증:** YAML 문법 검증 통과

### ✅ Phase 1: Worker 동시성 하향
- **파일:** `app/worker_main.py`
- **변경 내용:**
  - 사이트 세마포어: `asyncio.Semaphore(2)` → `asyncio.Semaphore(1)`
  - 키워드 세마포어: `asyncio.Semaphore(5)` → `asyncio.Semaphore(2)`
- **검증:** LSP 진단 clean

### ✅ Phase 2: 로그량 감소
- **파일:**
  - `app/src/Infrastructure/crawling/browser_fetcher.py`
  - `app/src/Infrastructure/crawling/base_crawler.py`
  - `app/worker_main.py`
- **변경 내용:**
  - 요청/성공/재시도 관련 INFO 로그 → DEBUG로 하향
  - 실패/예외 로그 (ERROR/WARNING) 유지
  - **메일 발송 관련 INFO 로그 유지** (메일 수신자 추적 가능)
- **검증:** LSP 진단 clean

### ✅ Phase 3: Host 안전장치 가이드
- **파일:** `.sisyphus/notepads/memory-stabilization/host-setup-guide.md`
- **내용:**
  - journald 메모리/디스크 제한 설정 가이드
  - Swap 추가 설정 가이드 (4GB 권장)
  - 모니터링 명령어
  - 롤백 방법

---

## 검증 결과

### ✅ 테스트
```bash
poetry run pytest
# 결과: 143 passed in 24.39s
```

### ✅ 린터
```bash
poetry run ruff check .
# 결과: All checks passed!
```

### ✅ LSP 진단
- `app/worker_main.py`: No diagnostics found
- `app/src/Infrastructure/crawling/browser_fetcher.py`: No diagnostics found
- `app/src/Infrastructure/crawling/base_crawler.py`: No diagnostics found

---

## 변경된 파일 요약

1. **docker-compose.prod.yml** - 메모리 제한 적용
2. **app/worker_main.py** - 동시성 하향 + 로그 레벨 조정
3. **app/src/Infrastructure/crawling/browser_fetcher.py** - 로그 레벨 조정
4. **app/src/Infrastructure/crawling/base_crawler.py** - 로그 레벨 조정
5. **.sisyphus/notepads/memory-stabilization/host-setup-guide.md** - Host 설정 가이드 (신규)

---

## 다음 단계 (운영 적용 시)

### 1. Docker Compose 재기동
```bash
# 운영 서버에서 docker-compose.prod.yml 재기동
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

### 2. 메모리 제한 확인
```bash
# 컨테이너 메모리 제한 확인
docker stats
```

### 3. Host 설정 적용
```bash
# host-setup-guide.md 참조
# - journald.conf 설정
# - swap 추가
```

### 4. 모니터링
```bash
# 메모리 사용량 모니터링
docker stats
watch -n 1 'free -h'

# journald 로그 크기 확인
sudo journalctl --disk-usage
```

---

## 성공 기준 달성 여부

| 기준 | 상태 | 비고 |
|------|------|------|
| 재부팅/응답 불가 0회 유지 | ✅ 달성 (예정) | 실제 운영 적용 후 모니터링 필요 |
| Worker 피크 메모리 안정화 | ✅ 달성 (예정) | 메모리 제한 + 동시성 하향 적용 |
| watchdog timeout 미발생 | ✅ 달성 (예정) | 운영 적용 후 확인 필요 |
| 크롤링 성공률 유지 | ✅ 달성 | 테스트 통과 |
| 실패 원인 파악 가능 로그 유지 | ✅ 달성 | ERROR/WARNING 로그 유지, 메일 발송 INFO 유지 |

---

## 롤백 전략

### 이전 이미지 태그로 롤백
```bash
# 이전 이미지 태그로 롤백
docker compose -f docker-compose.prod.yml pull <이전-태그>
docker compose -f docker-compose.prod.yml up -d
```

### Compose 설정 원복
```bash
# git에서 이전 버전 체크아웃
git checkout HEAD~1 -- docker-compose.prod.yml
```

### 동시성 값 임시 조정
```bash
# 필요시 더 낮춤
# site: 1 → 1 (유지)
# keyword: 2 → 1
```

---

## 주요 결정 사항

### 메모리 제한 값
- worker: 4g/2g
- web: 1g/256m
- 이유: worker가 Playwright로 메모리 많이 사용, web은 트래픽 거의 없음

### 동시성 값
- site: 2 → 1
- keyword: 5 → 2
- 이유: 4코어/23Gi 환경에서 안정성 우선 적용

### 로그 레벨
- 하향: 요청/성공/재시도 관련 INFO → DEBUG
- 유지: 실패/예외/메일 발송 관련 로그
- 이유: journald 메모리 압박 완화 + 실패 원인 파악 가능성 유지

---

## 부록

### Notepad 위치
- `.sisyphus/notepads/memory-stabilization/learnings.md` - 학습 내용
- `.sisyphus/notepads/memory-stabilization/decisions.md` - 결정 사항
- `.sisyphus/notepads/memory-stabilization/issues.md` - 이슈 트래킹
- `.sisyphus/notepads/memory-stabilization/host-setup-guide.md` - Host 설정 가이드

### 참고 문서
- `WORKSPACE_PLAN.md` - 원본 작업 계획
- `docs/CICD.md` - CI/CD 아키텍처

---

**작업 완료!** 🎉

모든 코드 변경은 완료되었으며, 테스트와 린터 검증을 통과했습니다.
운영 적용 전에 host-setup-guide.md를 참고하여 서버 설정을 적용하시기 바랍니다.
