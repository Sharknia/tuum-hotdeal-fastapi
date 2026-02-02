# 다중 세션 지원 및 토큰 해싱 보안 강화 (Multi-Session Auth)

## TL;DR

> **요약**: 단일 세션 제한을 제거하고, 기기별 다중 로그인을 지원하는 구조로 변경합니다. 동시에 보안 강화를 위해 토큰 원본 대신 해시값을 저장합니다.
> 
> **Deliverables**:
> - `refresh_tokens` 테이블 신설 (1:N 관계)
> - 토큰 해싱 저장 및 검증 로직 (SHA-256)
> - 세션 제한 로직 (최대 5개, FIFO 삭제)
> - 마이그레이션 스크립트 (기존 토큰 데이터 초기화)
> 
> **Estimated Effort**: Medium (DB 스키마 변경 및 핵심 인증 로직 수정)
> **Risk**: High (배포 시 모든 사용자 강제 로그아웃 발생 - **승인됨**)

---

## Context

### Background
현재 시스템은 `User` 테이블에 `refresh_token` 컬럼이 하나만 존재하여, 새 기기에서 로그인하면 기존 기기의 토큰을 덮어써서 로그아웃되는 문제가 있습니다. 또한 토큰이 평문(JWT)으로 저장되어 DB 유출 시 보안 위험이 존재합니다.

### Key Decisions (Confirmed)
1.  **마이그레이션 전략: Option A (Cool Initialization)**
    - 기존 `User.refresh_token` 데이터를 마이그레이션하지 않고 **삭제**합니다.
    - 배포 시 모든 사용자는 1회 다시 로그인해야 합니다.
    - 이유: 구현 복잡도 최소화 및 레거시 코드 즉시 제거.

2.  **보안 전략: Option B (Hash Storage)**
    - DB에 토큰 원본을 저장하지 않고 **SHA-256 해시값**만 저장합니다.
    - `refresh_token` 쿠키 탈취는 여전히 위험하지만, DB 탈취 시 공격자가 토큰을 위조/사용할 수 없습니다.

3.  **세션 정책**
    - **Max Sessions**: 사용자당 최대 **5개** 세션 유지.
    - **Eviction Policy**: 6번째 로그인 시 **가장 오래된(Created First)** 세션을 자동 삭제.

---

## Work Objectives

### Core Objective
- 사용자가 PC, 모바일, 태블릿 등 여러 기기에서 동시에 로그인 상태를 유지할 수 있어야 한다.
- DB가 유출되더라도 공격자가 유효한 리프레시 토큰을 획득할 수 없어야 한다.

### Must Have
- `refresh_tokens` 테이블 (1:N)
- 토큰 해싱 저장 (SHA-256)
- 최대 세션 수 제한 (5개) 로직
- User-Agent 저장 (기기 식별용)

### Must NOT Have
- 복잡한 무중단 마이그레이션 로직 (기존 컬럼 유지 등 금지)
- 토큰 원본 DB 저장

---

## Verification Strategy

### Test Strategy
- **Infrastructure**: `pytest` + `pytest-asyncio`
- **Type**: TDD 권장 (인증 로직은 중요하므로 테스트 먼저 작성)

### Manual Verification Scenarios (필수)
1.  **다중 로그인 테스트**:
    - Chrome(Secret mode)에서 로그인 → 유지
    - Firefox에서 로그인 → 유지
    - Chrome에서 새로고침(토큰 갱신) → 유지 (기존에는 여기서 풀림)
2.  **세션 제한 테스트**:
    - `MAX_SESSION=2`로 임시 설정 후 3번째 기기 로그인
    - 1번째 기기 로그아웃 확인
3.  **로그아웃 테스트**:
    - 특정 기기 로그아웃 시 해당 기기만 풀리는지 확인

---

## Execution Strategy (Waves)

```
Wave 1 (Database):
└── Task 1: Create RefreshToken Model & Migration [Blocking]
    (이 단계 이후 DB 스키마가 변경되므로 코드 수정 전까지 서버 에러 발생 가능)

Wave 2 (Repository & Logic):
├── Task 2: Implement Hash Utils & Repository Logic
└── Task 3: Update Auth Dependencies & Services (Session Limit)

Wave 3 (Cleanup & Verify):
└── Task 4: Integration Test & Manual Verification
```

---

## TODOs

- [x] 1. **[DB] RefreshToken 모델 생성 및 마이그레이션**
    **What to do**:
    - `app/src/domain/user/models.py`:
        - `RefreshToken` 클래스 추가 (Base 상속)
        - 필드: `id(UUID)`, `user_id(FK)`, `token_hash(String 64)`, `user_agent(String)`, `expires_at(DateTime)`, `created_at`
        - `User` 모델에서 `refresh_token` 컬럼 삭제 및 `relationship` 추가
    - `alembic/`:
        - `alembic revision --autogenerate -m "add_refresh_tokens_table_and_remove_column"` 실행
        - 생성된 스크립트 확인 (User 컬럼 삭제 포함되었는지)

    **References**:
    - `app/src/domain/user/models.py`: 기존 User 모델 참조
    - `app/src/core/database.py`: Base 클래스 참조

    **Acceptance Criteria**:
    - [x] `alembic upgrade head` 실행 시 에러 없이 DB 스키마 변경
    - [x] DB 툴(DBeaver 등) 확인 시 `refresh_tokens` 테이블 생성됨

- [x] 2. **[Repo] 레포지토리 로직 전면 재작성 (해싱 적용)**
    **What to do**:
    - `app/src/core/security.py`: `get_token_hash(token: str) -> str` 헬퍼 함수 추가 (hashlib sha256 사용)
    - `app/src/domain/user/repositories.py`:
        - `save_refresh_token`: 
            1. 만료된 토큰 일괄 삭제 (Cleanup)
            2. 현재 활성 세션 수 카운트 (`SELECT count(*)`)
            3. 5개 이상이면 가장 오래된 것 삭제 (`DELETE ... ORDER BY created_at ASC LIMIT 1`)
            4. 새 토큰 해싱 후 `INSERT`
        - `verify_refresh_token`: 입력된 토큰을 해싱하여 `token_hash` 컬럼과 비교 조회
        - `delete_refresh_token`: 특정 토큰(해시값 기준)만 삭제
        - `delete_all_tokens`: 해당 유저의 모든 토큰 삭제 (관리용/비밀번호 변경 시용)

    **References**:
    - `app/src/domain/user/repositories.py`: 기존 로직 참조 (전면 수정 필요)
    - `hashlib`: Python 표준 라이브러리 사용

    **Acceptance Criteria**:
    - [x] `save_refresh_token` 호출 시 DB에 암호화된 문자열이 저장되어야 함
    - [x] 세션이 5개 꽉 찼을 때 추가 저장 시, 총 개수가 5개로 유지되어야 함

- [x] 3. **[Auth] 인증 서비스 및 의존성 수정**
    **What to do**:
    - `app/src/core/dependencies/auth.py`:
        - `create_refresh_token`: `user_agent` 파라미터 추가 (Request 객체에서 추출)
        - `delete_refresh_token`: 쿠키에 있는 토큰 값으로 특정 세션만 로그아웃 처리
        - `authenticate_refresh_token`: 로직 흐름 유지하되, 내부적으로 리포지토리의 해시 검증 로직 호출
    - `app/src/domain/user/services.py`:
        - `login_user`: `request.headers.get("user-agent")` 추출하여 레포지토리에 전달
        - `logout_user`: 인자 전달 수정
    - `app/src/domain/user/v1/router.py`:
        - 엔드포인트에서 `Request` 객체를 받아 서비스에 전달하도록 수정

    **References**:
    - `app/src/core/dependencies/auth.py`: 인증 의존성
    - `fastapi.Request`: User-Agent 헤더 추출용

    **Acceptance Criteria**:
    - [x] 로그인 시 `refresh_tokens` 테이블에 `user_agent` 값이 정상적으로 기록됨
    - [x] 로그아웃 시 해당 기기의 토큰만 DB에서 사라짐

- [x] 4. **[Test] 통합 테스트 및 검증**
    **What to do**:
    - `tests/domain/user/test_multi_session_auth.py` (신규 생성 또는 기존 수정):
        - 테스트 케이스 1: A기기 로그인 -> B기기 로그인 -> 둘 다 인증 성공 확인
        - 테스트 케이스 2: 6개 기기 로그인 -> 1번째 기기 인증 실패 확인 (FIFO 동작)
        - 테스트 케이스 3: 로그아웃 후 해당 토큰 재사용 불가 확인

    **Acceptance Criteria**:
    - [x] `poetry run pytest` 실행 시 모든 테스트 통과
    - [x] 실제 브라우저 2개(일반/시크릿)에서 로그인 유지 확인

---

## Commit Strategy
- `feat(db): add refresh_tokens table and migrate`
- `feat(auth): implement token hashing and multi-session repository logic`
- `feat(user): update login service to support multi-device session`
- `test(auth): add multi-session integration tests`
