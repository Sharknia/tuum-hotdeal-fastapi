# Memory Stabilization - Learnings

## Phase 0 - Compose Memory Limits
- `deploy.resources.limits`는 일반 docker compose에서 무시됨
- `mem_limit`, `mem_reservation`을 사용해야 실제 제한 적용됨
- 서버 사양: 4코어/23Gi RAM/Swap 없음

## Phase 1 - Worker Concurrency
- 현재 세마포어: site=2, keyword=5
- Playwright 기반 크롤링으로 메모리 스파이크 발생
- 동시성 낮추는 것이 가장 즉각적인 효과

## Phase 2 - Logging
- INFO 로그가 매우 많아 journald 메모리 압박
- 실패 원인/메일 수신자 로그는 유지 필요
- 요청/성공 관련 반복 INFO는 DEBUG로 하향

## General
- 모든 작업은 커밋/푸시 없이 코드 변경만 진행
- 각 Phase 완료 후 LSP 진단으로 검증

## Phase 0 완료 (2026-02-02)
- docker-compose.prod.yml에 메모리 제한 적용 완료
- web: 1g/256m, worker: 4g/2g
- deploy.resources.limits 제거 완료
- YAML 문법 검증 통과

## Phase 1 완료 (2026-02-02)
- app/worker_main.py 세마포어 값 하향 완료
- site: 2→1, keyword: 5→2
- LSP 진단 clean

## Phase 2 완료 (2026-02-02)
- BrowserFetcher 로그 하향: 요청/성공/챌린지 재시도 INFO → DEBUG
- BaseCrawler 로그 하향: 요청/성공/브라우저/프록시 INFO → DEBUG
- worker_main.py 로그 하향: 키워드 처리/진행 INFO → DEBUG
- 메일 발송 관련 INFO 로그는 유지
- 모든 파일 LSP 진단 clean

## Phase 3 완료 (2026-02-02)
- Host 안전장치 설정 가이드 작성 완료
- journald 메모리/디스크 제한 설정 가이드
- Swap 추가 설정 가이드
- 롤백 방법 포함

## 최종 검증 완료 (2026-02-02)
- pytest: 143 passed ✅
- ruff check: All checks passed ✅
- LSP 진단: 모든 Python 파일 clean ✅
