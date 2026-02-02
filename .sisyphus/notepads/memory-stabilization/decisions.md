# Memory Stabilization - Decisions

## Memory Limits (Phase 0)
- worker: mem_limit=4g, mem_reservation=2g
- web: mem_limit=1g, mem_reservation=256m
- 이유: worker가 Playwright로 메모리 많이 사용, web은 트래픽 거의 없음

## Concurrency (Phase 1)
- site semaphore: 2 → 1
- keyword semaphore: 5 → 2
- 이유: 4코어/23Gi 환경에서 안정성 우선 적용

## Logging (Phase 2)
- 하향 대상: 요청/성공/재시도 관련 INFO 로그
- 유지 대상: 실패/예외/메일 발송 관련 로그

## Host Configuration (Phase 3)
- journald.conf: SystemMaxUse=500M, RuntimeMaxUse=100M, SystemMaxFileSize=50M
- Swap: 4GB 추가 권장 (swappiness=10)
- 모든 설정은 host-setup-guide.md에 문서화
