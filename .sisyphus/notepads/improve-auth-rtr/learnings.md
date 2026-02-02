
## Schema & Dependency Refactoring (2026-01-28)

### 패턴: Optional 필드로 호환성 유지
- `AuthenticatedUser` 모델에 `token_hash: str | None = None` 추가
- 기존 의존성(`registered_user`, `authenticate_user`)과 호환성 유지
- 리프레시 토큰 검증 시에만 해시 값 전달

### 주의사항: 중요한 보안 필드 주석
- RTR 기능과 같은 보안 관련 필드는 주석이 필요
- 필드의 용도와 언제 전달되는지 명확히 설명

### 구현 순서
1. Schema 먼저 수정 (필드 추가)
2. Dependency 수정 (해시 계산 및 전달)
3. import 추가 필요 (`get_token_hash` from `app.src.core.security`)

## Repository Function Design Pattern (2026-01-28 02:53)

### 패턴: 이미 해시된 값으로 작업하는 별도 함수 추가
- 기존 `delete_refresh_token`: 원본 토큰 받아 → 해싱 후 삭제
- 신규 `delete_token_by_hash`: 이미 해시된 값 받아 → 직접 삭제
- 용도가 다르면 별도 함수로 분리 (인터페이스 명확화)

### 패턴: Repository 함수 Docstring 필수
- 공개 API인 경우 Docstring 필수
- 함수 이름만으로는 인자가 이미 해시된 값인지 명확하지 않음
- RTR 전용 함수임을 명시

## Service Layer RTR Implementation (2026-01-28 02:53)

### 패턴: "삭제 후 생성" 순서 중요
- RTR에서 토큰 삭제는 신규 토큰 생성 전에 실행
- 순서 반전 시 보안 취약점 (토큰 재사용 공격)
- 이 로직이 보안 기능임을 주석으로 명시

### 패턴: Optional 파라미터로 하위 호환성 유지
- `refresh_access_token`에 `token_hash: str | None = None` 추가
- 기존 코드와 호환성 유지
- `if token_hash:` 체크로 조건부 삭제

### 패턴: 트랜잭션 관리
- 서비스 함수 레벨에서 이미 트랜잭션 처리됨
- 추가적인 트랜잭션 관리 불필요
- Repository 함수 내에서 `commit()` 호출

## Router Parameter Passing (2026-01-28 02:53)

### 패턴: 의존성 객체에서 필드 추출하여 전달
- 라우터: `refresh_user.token_hash` 추출
- 서비스: `token_hash` 파라미터로 받아 처리
- 객체 전체 전달 대신 필요한 필드만 전달 (명확한 인터페이스)
