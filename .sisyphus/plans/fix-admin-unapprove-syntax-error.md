# 관리자 페이지 "승인 해제" SyntaxError 버그 수정

## TL;DR

> **Quick Summary**: 관리자 페이지에서 UUID가 따옴표 없이 onclick 핸들러에 삽입되어 발생하는 JavaScript SyntaxError를 수정합니다.
> 
> **Deliverables**:
> - `static/js/admin.js` 106번, 108번 줄 수정 (UUID를 문자열로 처리)
> 
> **Estimated Effort**: Quick
> **Parallel Execution**: NO - sequential (단일 파일, 2줄 수정)
> **Critical Path**: Task 1 (수정) → Task 2 (검증)

---

## Context

### Original Request
관리자페이지에서 "승인 해제" 기능 작동 안함. 개발자 도구에서 `Uncaught SyntaxError: Invalid or unexpected token` 로그가 확인됨.

### Interview Summary
**Key Discussions**:
- 문제 원인: `admin.js`에서 UUID를 onclick 핸들러에 삽입할 때 따옴표가 누락됨
- 영향 범위: 106번 줄 (`unapproveUser`), 108번 줄 (`approveUser`)

**Research Findings**:
- User 모델의 `id` 필드가 UUID 타입 (`UUID(as_uuid=True)`)
- 렌더링 시 `onclick="unapproveUser(550e8400-e29b-...)"` 형태가 되어 JS 파서 오류 발생
- 백엔드 API는 UUID를 문자열로 받아도 자동 변환하므로 백엔드 수정 불필요

### Metis Review
**Identified Gaps** (addressed):
- `admin.js`가 빌드 산출물인지 확인 필요 → 직접 편집되는 정적 파일임을 확인
- 동일 패턴이 다른 곳에 있는지 전수 조사 필요 → 156번 줄 `deleteKeyword`는 Integer ID이므로 문제 없음

---

## Work Objectives

### Core Objective
UUID를 onclick 핸들러에 문자열로 올바르게 삽입하여 JavaScript SyntaxError를 해결합니다.

### Concrete Deliverables
- `static/js/admin.js` 수정 완료

### Definition of Done
- [x] 관리자 페이지에서 "승인 해제" 버튼 클릭 시 SyntaxError 발생하지 않음
- [x] 관리자 페이지에서 "승인" 버튼 클릭 시 SyntaxError 발생하지 않음
- [x] `poetry run ruff check .` 통과
- [x] `poetry run pytest` 통과

### Must Have
- 106번 줄: `${user.id}` → `'${user.id}'`
- 108번 줄: `${user.id}` → `'${user.id}'`

### Must NOT Have (Guardrails)
- 백엔드 코드 변경
- UI/스타일 변경
- 다른 기능에 대한 변경
- 불필요한 리팩토링

---

## Verification Strategy (MANDATORY)

### Test Decision
- **Infrastructure exists**: YES (poetry run pytest)
- **User wants tests**: Manual-only (프론트엔드 JS 버그이므로 자동화된 명령 검증)
- **Framework**: pytest (백엔드), 브라우저 수동 검증 (프론트엔드)

### Automated Verification Only (NO User Intervention)

> **CRITICAL PRINCIPLE: ZERO USER INTERVENTION**
> 
> 모든 검증은 에이전트가 직접 실행할 수 있는 명령으로 수행됩니다.

**By Deliverable Type:**

| Type | Verification Tool | Automated Procedure |
|------|------------------|---------------------|
| **JavaScript 파일 수정** | Bash (grep) | 수정된 패턴이 파일에 존재하는지 확인 |
| **린트/테스트** | Bash | ruff, pytest 실행 |

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Start Immediately):
└── Task 1: admin.js 수정 (106번, 108번 줄)

Wave 2 (After Wave 1):
└── Task 2: 검증 (패턴 확인 + 린트/테스트)
```

### Dependency Matrix

| Task | Depends On | Blocks | Can Parallelize With |
|------|------------|--------|---------------------|
| 1 | None | 2 | None |
| 2 | 1 | None | None (final) |

---

## TODOs

- [x] 1. admin.js UUID 문자열 처리 수정

  **What to do**:
  - 106번 줄: `onclick="unapproveUser(${user.id})"` → `onclick="unapproveUser('${user.id}')"`
  - 108번 줄: `onclick="approveUser(${user.id})"` → `onclick="approveUser('${user.id}')"`

  **Must NOT do**:
  - 다른 라인 수정
  - 코드 스타일 변경
  - 리팩토링

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 단일 파일 2줄 수정의 단순 버그 픽스
  - **Skills**: []
    - 특별한 스킬 불필요 (단순 텍스트 수정)

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (Sequential)
  - **Blocks**: Task 2
  - **Blocked By**: None (can start immediately)

  **References** (CRITICAL - Be Exhaustive):

  **Pattern References** (existing code to follow):
  - `static/js/admin.js:106` - 수정 대상 라인 (unapproveUser)
  - `static/js/admin.js:108` - 수정 대상 라인 (approveUser)
  - `static/js/admin.js:114` - 참고: URL 파라미터에서는 따옴표 없이 UUID 사용해도 됨 (문자열 컨텍스트)

  **API/Type References** (contracts to implement against):
  - `app/src/domain/admin/v1/router.py:46` - `user_id: UUID` 파라미터 (문자열을 자동 변환)
  - `app/src/domain/admin/v1/router.py:60` - unapprove 엔드포인트

  **WHY Each Reference Matters**:
  - 106번, 108번 줄은 직접 수정 대상이며, onclick 핸들러에 UUID가 삽입되는 위치
  - 114번 줄은 URL 컨텍스트에서 UUID 사용 예시로, 따옴표가 필요 없는 경우를 보여줌
  - 백엔드 router.py는 UUID 타입 힌트가 문자열을 자동 파싱함을 확인

  **Acceptance Criteria**:

  **Automated Verification (ALWAYS include):**
  ```bash
  # 수정된 패턴이 존재하는지 확인
  grep -n "unapproveUser('\${user.id}')" static/js/admin.js
  # Assert: 출력에 106번 줄이 포함됨

  grep -n "approveUser('\${user.id}')" static/js/admin.js
  # Assert: 출력에 108번 줄이 포함됨
  ```

  **Evidence to Capture:**
  - [ ] grep 명령 실행 결과 (수정된 패턴 확인)

  **Commit**: YES
  - Message: `fix(admin): UUID 문자열 처리로 onclick SyntaxError 수정`
  - Files: `static/js/admin.js`
  - Pre-commit: `poetry run ruff check . && poetry run pytest`

---

- [x] 2. 린트 및 테스트 검증

  **What to do**:
  - Ruff 린트 실행
  - Pytest 테스트 실행
  - 결과 확인

  **Must NOT do**:
  - 테스트 실패 시 무시
  - 린트 오류 무시

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: 표준 검증 명령 실행
  - **Skills**: []
    - 특별한 스킬 불필요

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (Sequential, after Task 1)
  - **Blocks**: None (final task)
  - **Blocked By**: Task 1

  **References**:
  - `AGENTS.md` - 검증 규칙: `poetry run pytest`, `poetry run ruff check .`

  **Acceptance Criteria**:

  **Automated Verification:**
  ```bash
  # 린트 검증
  poetry run ruff check .
  # Assert: Exit code 0

  # 테스트 검증
  poetry run pytest
  # Assert: Exit code 0, 모든 테스트 통과
  ```

  **Evidence to Capture:**
  - [ ] ruff 실행 결과 (exit code 0)
  - [ ] pytest 실행 결과 (모든 테스트 통과)

  **Commit**: NO (Task 1에서 이미 커밋)

---

## Commit Strategy

| After Task | Message | Files | Verification |
|------------|---------|-------|--------------|
| 1 | `fix(admin): UUID 문자열 처리로 onclick SyntaxError 수정` | static/js/admin.js | ruff + pytest |

---

## Success Criteria

### Verification Commands
```bash
# 패턴 확인
grep "unapproveUser('\${user.id}')" static/js/admin.js  # Expected: 매칭됨
grep "approveUser('\${user.id}')" static/js/admin.js    # Expected: 매칭됨

# 린트
poetry run ruff check .  # Expected: exit 0

# 테스트
poetry run pytest        # Expected: all passed
```

### Final Checklist
- [x] 106번 줄 수정 완료 (unapproveUser)
- [x] 108번 줄 수정 완료 (approveUser)
- [x] 린트 통과
- [x] 테스트 통과
- [x] SyntaxError 더 이상 발생하지 않음
