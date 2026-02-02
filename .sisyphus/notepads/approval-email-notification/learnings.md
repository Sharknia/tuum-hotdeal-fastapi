# 학습 내용: 가입 승인 알림 메일

## 2026-01-30: send_approval_notification() 함수 구현

### 발견한 패턴
1. **메일 발송 함수 구조**: `send_new_user_notifications()` 패턴을 따름
   - async 함수 형태
   - f-string으로 메일 제목/본문 생성
   - try-except로 에러 로깅 (logger.error 사용)
   - send_email() 호출은 별도 처리 없이 사용

2. **send_email() 함수 시그니처** (`app/src/Infrastructure/mail/mail_manager.py:45-72`)
   - `subject: str` - 필수
   - `to: str` - 필수
   - `body: str = ""` - 선택 (기본값: 빈 문자열)
   - `sender: str = settings.SMTP_FROM` - 선택
   - `is_html: bool = False` - 선택 (기본값: False, 텍스트 메일)

3. **간단한 텍스트 메일 형식**
   - HTML 없이 일반 텍스트로 충분
   - 서비스 링크: https://hotdeal.tuum.day
   - 환영 메시지 + 닉네임 포함

### 성공적 접근 방식
- 기존 함수 패턴을 그대로 따르는 것이 빠르고 안전함
- LSP diagnostics로 즉시 검증 (오류 없음)
- 간단한 텍스트 형식으로 복잡도 최소화

## 2026-01-30: approve_user()에 메일 발송 로직 통합

### 발견한 사항
1. **activate_user()의 내장된 중복 방지 로직**
   - `app/src/domain/user/repositories.py:65-80`
   - 이미 `if user and not user.is_active` 조건으로 중복 승인 방지
   - is_active가 True인 사용자에 대해 activate_user() 호출 시 None 반환

2. **메일 발송 통합 패턴**
   - 승인 전 상태 확인: `get_user_by_id()`로 현재 is_active 저장
   - activate_user() 호출 후 결과 확인
   - was_inactive가 True일 때만 메일 발송
   - try-except로 감싸서 메일 실패 시에도 승인 유지

3. **필요한 import**
   - `from app.src.domain.user.repositories import get_user_by_id`
   - `from app.src.domain.user.services import send_approval_notification`

### 구현 로직
```python
# 승인 전 사용자 상태 확인 (중복 메일 발송 방지)
existing_user = await get_user_by_id(db, user_id)
if not existing_user:
    raise AuthErrors.USER_NOT_FOUND

was_inactive = not existing_user.is_active

# 사용자 승인 처리
user = await activate_user(db, user_id)
if not user:
    raise AuthErrors.USER_NOT_FOUND

# 첫 승인인 경우에만 메일 발송
if was_inactive:
    try:
        await send_approval_notification(user_email=user.email, user_nickname=user.nickname)
    except Exception:
        # 메일 발송 실패해도 승인은 유지
        pass

return user
```

### 검증 방법
- grep으로 import 및 함수 사용 확인
- LSP diagnostics로 코드 오류 검사 (오류 없음)
- 응답 스키마 변경 없음 (UserResponse 유지)
