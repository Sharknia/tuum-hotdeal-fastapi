# 승인 알림 메일 기능 추가

## TL;DR

> **Quick Summary**: 관리자가 사용자를 승인할 때, 해당 사용자에게 승인 완료 알림 메일을 발송합니다.
> 
> **Deliverables**:
> - `app/src/domain/user/services.py`에 `send_approval_notification()` 함수 추가
> - `app/src/domain/admin/v1/router.py`에서 승인 후 메일 발송 호출
> - 단위 테스트 추가
> 
> **Estimated Effort**: Short
> **Parallel Execution**: NO - sequential (의존성 있음)
> **Critical Path**: Task 1 (서비스 함수) → Task 2 (라우터 통합) → Task 3 (테스트) → Task 4 (검증)

---

## Context

### Original Request
관리자가 사용자를 승인할 때, 유저에게 승인되었음을 알리는 메일 발송

### Interview Summary
**Key Discussions**:
- 메일 발송 실패 시: 승인 상태는 유지, 에러 로그만 기록
- 중복 발송: 이미 승인된 사용자는 메일 발송 안함 (첫 승인만)
- 메일 형식: 간단한 텍스트 (HTML 없음)

**Research Findings**:
- 기존 메일 인프라: `send_email()` in `mail_manager.py`
- 기존 패턴: `send_new_user_notifications()` in `user/services.py`
- 승인 로직: `approve_user()` in `admin/v1/router.py`
- `UserResponse`에 `email`, `nickname`, `is_active` 필드 존재

### Metis Review
**Identified Gaps** (addressed):
- 메일 실패 정책 → 승인 유지 + 로그
- 중복 발송 방지 → 승인 전 `is_active` 체크
- 서비스 링크 → 환경변수 또는 하드코딩 URL

---

## Work Objectives

### Core Objective
승인된 사용자에게 알림 메일을 발송하여 서비스 이용 시작을 유도합니다.

### Concrete Deliverables
- `send_approval_notification()` 함수
- `approve_user()` 엔드포인트에 메일 발송 통합
- 단위 테스트

### Definition of Done
- [x] 승인 시 사용자에게 메일 발송됨
- [x] 이미 승인된 사용자는 메일 발송 안됨
- [x] 메일 실패해도 승인은 유지됨
- [x] `poetry run ruff check .` 통과
- [x] `poetry run pytest` 통과

### Must Have
- 승인 완료 알림 메일 발송 기능
- 중복 발송 방지 (첫 승인만)
- 메일 실패 시 에러 로깅

### Must NOT Have (Guardrails)
- 승인 로직의 응답 스키마 변경
- HTML 템플릿 시스템 도입
- 비동기 큐/재시도 인프라 도입
- 다국어 지원

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: YES (poetry run pytest)
- **User wants tests**: YES (TDD 방식)
- **Framework**: pytest + pytest-mock

### Automated Verification Only (NO User Intervention)

| Type | Verification Tool | Automated Procedure |
|------|------------------|---------------------|
| **서비스 함수** | pytest | 단위 테스트 작성 및 실행 |
| **API 통합** | pytest | 통합 테스트 작성 및 실행 |
| **린트/테스트** | Bash | ruff, pytest 실행 |

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately):
└── Task 1: send_approval_notification() 함수 추가

Wave 2 (After Wave 1):
└── Task 2: approve_user() 라우터에 메일 발송 통합

Wave 3 (After Wave 2):
└── Task 3: 단위 테스트 추가

Wave 4 (After Wave 3):
└── Task 4: 린트 및 테스트 검증
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2, 3 | None |
| 2 | 1 | 3 | None |
| 3 | 1, 2 | 4 | None |
| 4 | 3 | None | None (final) |

---

## TODOs

- [x] 1. send_approval_notification() 함수 추가

  **What to do**:
  - `app/src/domain/user/services.py`에 함수 추가
  - 기존 `send_new_user_notifications()` 패턴 따름
  - 간단한 텍스트 메일 형식

  **함수 시그니처**:
  ```python
  async def send_approval_notification(user_email: str, user_nickname: str) -> None:
      """승인된 사용자에게 알림 메일 발송"""
  ```

  **메일 내용**:
  - 제목: `[Tuum] 가입이 승인되었습니다`
  - 본문:
    ```
    {nickname}님, 환영합니다!
    
    Tuum 서비스 가입이 승인되었습니다.
    지금 바로 서비스를 이용해보세요.
    
    서비스 바로가기: https://hotdeal.tuum.day
    ```

  **Must NOT do**:
  - HTML 템플릿 사용
  - 새로운 의존성 추가
  - 기존 함수 수정

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 단순 함수 추가, 기존 패턴 따름
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1
  - **Blocks**: Task 2, 3
  - **Blocked By**: None

  **References**:
  - `app/src/domain/user/services.py:171-182` - `send_new_user_notifications()` 패턴
  - `app/src/Infrastructure/mail/mail_manager.py:45-72` - `send_email()` 함수

  **WHY Each Reference Matters**:
  - `send_new_user_notifications()`는 동일한 패턴으로 구현할 참조 코드
  - `send_email()`은 실제 호출할 함수의 시그니처 확인

  **Acceptance Criteria**:
  ```bash
  # 함수가 존재하는지 확인
  grep -n "async def send_approval_notification" app/src/domain/user/services.py
  # Assert: 함수 정의가 출력됨
  
  # send_email import 확인
  grep -n "from app.src.Infrastructure.mail.mail_manager import send_email" app/src/domain/user/services.py
  # Assert: import 문이 존재함 (이미 있을 수 있음)
  ```

  **Commit**: NO (Task 2와 함께 커밋)

---

- [x] 2. approve_user() 라우터에 메일 발송 통합

  **What to do**:
  - `app/src/domain/admin/v1/router.py`의 `approve_user()` 수정
  - 승인 전 `is_active` 상태 확인하여 중복 발송 방지
  - 승인 성공 후 메일 발송 (try-except로 감싸서 실패해도 승인 유지)

  **수정 로직**:
  ```python
  @router.patch("/users/{user_id}/approve", ...)
  async def approve_user(...):
      # 1. 현재 사용자 상태 확인 (중복 발송 방지용)
      # 2. 승인 처리
      user = await activate_user(db, user_id)
      if not user:
          raise AuthErrors.USER_NOT_FOUND
      # 3. 첫 승인인 경우에만 메일 발송 (is_active가 False → True)
      # 4. 메일 발송 (try-except로 감싸서 실패해도 승인 유지)
      return user
  ```

  **중복 발송 방지 로직**:
  - 승인 전 사용자의 `is_active` 상태를 먼저 확인
  - `is_active=False`였던 경우에만 메일 발송
  - 이미 `is_active=True`면 메일 발송 스킵

  **Must NOT do**:
  - 응답 스키마 변경
  - 다른 엔드포인트 수정
  - 트랜잭션 구조 변경

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 기존 함수에 몇 줄 추가
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 3
  - **Blocked By**: Task 1

  **References**:
  - `app/src/domain/admin/v1/router.py:44-53` - 현재 `approve_user()` 구현
  - `app/src/domain/user/repositories.py:116-122` - `is_active` 체크 가능한 함수 확인

  **Acceptance Criteria**:
  ```bash
  # 메일 발송 호출이 존재하는지 확인
  grep -n "send_approval_notification" app/src/domain/admin/v1/router.py
  # Assert: 함수 호출이 출력됨
  
  # try-except로 감싸져 있는지 확인
  grep -A5 "send_approval_notification" app/src/domain/admin/v1/router.py
  # Assert: except 블록이 존재함
  ```

  **Commit**: YES
  - Message: `feat(admin): 사용자 승인 시 알림 메일 발송 기능 추가`
  - Files: `app/src/domain/user/services.py`, `app/src/domain/admin/v1/router.py`
  - Pre-commit: `poetry run ruff check . && poetry run pytest`

---

- [x] 3. 단위 테스트 추가

  **What to do**:
  - `tests/domain/user/` 또는 `tests/domain/admin/`에 테스트 추가
  - `send_approval_notification()` 함수 테스트
  - `approve_user()` 엔드포인트에서 메일 발송 테스트

  **테스트 케이스**:
  1. 승인 성공 시 메일 발송 호출됨
  2. 이미 승인된 사용자는 메일 발송 안됨
  3. 메일 발송 실패해도 승인은 성공함

  **Must NOT do**:
  - 기존 테스트 수정
  - 실제 메일 발송 (mock 사용)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 기존 테스트 패턴 따름
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 4
  - **Blocked By**: Task 1, 2

  **References**:
  - `tests/domain/user/test_admin_notification.py` - 기존 알림 관련 테스트
  - `tests/domain/admin/test_user_mgmt.py` - 기존 사용자 관리 테스트

  **Acceptance Criteria**:
  ```bash
  # 테스트 파일에서 approval 관련 테스트 확인
  grep -rn "approval" tests/
  # Assert: 새 테스트 케이스가 존재함
  
  # pytest 실행
  poetry run pytest tests/ -v -k "approval"
  # Assert: 테스트 통과
  ```

  **Commit**: YES
  - Message: `test(admin): 승인 알림 메일 테스트 추가`
  - Files: `tests/domain/admin/test_approval_notification.py` (또는 기존 파일에 추가)

---

- [x] 4. 린트 및 테스트 검증

  **What to do**:
  - Ruff 린트 실행
  - Pytest 전체 테스트 실행
  - 결과 확인

  **Must NOT do**:
  - 테스트 실패 시 무시
  - 린트 오류 무시

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 표준 검증 명령 실행
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 4 (final)
  - **Blocks**: None
  - **Blocked By**: Task 3

  **References**:
  - `AGENTS.md` - 검증 규칙

  **Acceptance Criteria**:
  ```bash
  # 린트 검증
  poetry run ruff check .
  # Assert: Exit code 0
  
  # 테스트 검증
  poetry run pytest
  # Assert: Exit code 0, 모든 테스트 통과
  ```

  **Commit**: NO (이미 커밋됨)

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 2 | `feat(admin): 사용자 승인 시 알림 메일 발송 기능 추가` | services.py, router.py | ruff + pytest |
| 3 | `test(admin): 승인 알림 메일 테스트 추가` | test_*.py | ruff + pytest |

---

## Success Criteria

### Verification Commands
```bash
# 함수 존재 확인
grep -n "send_approval_notification" app/src/domain/user/services.py

# 라우터 통합 확인
grep -n "send_approval_notification" app/src/domain/admin/v1/router.py

# 린트
poetry run ruff check .

# 테스트
poetry run pytest
```

### Final Checklist
- [x] `send_approval_notification()` 함수 추가됨
- [x] `approve_user()`에서 메일 발송 호출됨
- [x] 중복 발송 방지 로직 구현됨
- [x] 메일 실패 시 승인 유지됨
- [x] 테스트 통과
- [x] 린트 통과
