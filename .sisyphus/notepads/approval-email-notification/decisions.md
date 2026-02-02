# 결정 사항: 가입 승인 알림 메일

## 2026-01-30: 텍스트 메일 형식 채택

### 결정 내용
- **HTML 템플릿 미사용**: 간단한 텍스트 메일로 구현
- **기존 패턴 준수**: `send_new_user_notifications()`와 동일한 구조 사용
- **에러 처리**: try-except로 래핑하여 logger.error()에 기록

### 근거
1. **단순성**: 환영 메시지에는 복잡한 HTML이 필요 없음
2. **일관성**: 기존 알림 메일들도 텍스트 형식 사용
3. **유지보수성**: 템플릿 추가 없이 함수 하나로 해결
4. **신속성**: 별도 의존성 없이 즉시 구현 가능

### 함수 시그니처
```python
async def send_approval_notification(user_email: str, user_nickname: str) -> None
```
