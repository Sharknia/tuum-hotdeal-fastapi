# 작업 계획: tuum.day 핫딜 알림 프로젝트 생성

## 개요
현재 `llm-chat-client` 레포지토리에서 LLM 관련 코드를 제거하고, 핫딜 알림 서비스(tuum.day)를 위한 새 프로젝트를 생성합니다.

---

## 사전 질문 (작업 시작 전 확인 필요)

- [ ] **새 프로젝트 이름**: `tuum-day`? `tuum-hotdeal`? 다른 이름?
- [ ] **새 GitHub 레포지토리 생성 여부**: gh repo create 실행할 것인지?

---

## Phase 1: 프로젝트 복사

### Task 1.1: 디렉토리 복사
```bash
cp -r ~/dev/llm-chat-client ~/dev/{NEW_PROJECT_NAME}
cd ~/dev/{NEW_PROJECT_NAME}
```

### Task 1.2: Git 초기화 (기존 히스토리 제거)
```bash
rm -rf .git
git init
```

---

## Phase 2: LLM 관련 파일 제거

### 삭제 대상 파일들

#### 2.1 완전 삭제 (디렉토리)
| 경로 | 이유 |
|------|------|
| `app/src/llm/` | LLM 모델 인터페이스 (base.py, gemini.py, grok.py) |
| `app/src/clients/` | LLM 클라이언트 (chat_client.py) |

```bash
rm -rf app/src/llm
rm -rf app/src/clients
```

#### 2.2 완전 삭제 (개별 파일)
| 파일 | 이유 |
|------|------|
| `app/src/models/message.py` | LLM 메시지 모델 |
| `app/src/models/message_list.py` | LLM 메시지 리스트 |
| `exmaple.py` | LLM 예제 스크립트 |
| `static/chat.html` | LLM 채팅 UI (사용되지 않음) |

```bash
rm app/src/models/message.py
rm app/src/models/message_list.py
rm exmaple.py
rm static/chat.html
```

---

## Phase 3: 설정 파일 수정

### 3.1 pyproject.toml 수정
**수정 내용:**
- `name` 변경: `"grok-crobat"` → `"{NEW_PROJECT_NAME}"`
- `description` 추가: 핫딜 알림 서비스 설명
- **제거할 의존성:**
  - `openai (>=1.67.0,<2.0.0)` 
  - `google-genai (>=1.11.0,<2.0.0)`

### 3.2 Makefile 수정 (있다면)
- `example` 타겟 제거

### 3.3 .env.example 검토
- LLM API 키 관련 항목 제거 (GROK_API_KEY, GOOGLE_API_KEY)

---

## Phase 4: main.py 정리

### 4.1 확인 필요 사항
- `app/main.py`에서 chat 라우트 제거 필요 여부 확인

```python
# 제거 대상 (line 127-129)
@app.get("/chat", response_class=FileResponse)
async def chat_page():
    return FileResponse("static/chat.html")
```

---

## Phase 5: README.md 재작성

### 새 README 구조

```markdown
# tuum.day - 핫딜 알림 서비스

사용자가 관심 키워드를 등록하면, 핫딜 사이트를 주기적으로 크롤링하여 
새로운 핫딜 발견 시 이메일로 알림을 보내주는 서비스입니다.

## 주요 기능

- 사용자 인증 (회원가입/로그인, JWT)
- 핫딜 키워드 등록/관리
- 알구몬(algumon.com) 핫딜 크롤링
- 새 핫딜 발견 시 이메일 알림
- 백그라운드 워커 (30분 주기 크롤링)

## 기술 스택

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Worker**: APScheduler, asyncio
- **Crawling**: BeautifulSoup, httpx
- **Email**: aiosmtplib
- **Auth**: JWT (python-jose), bcrypt
- **Frontend**: Vanilla HTML/CSS/JS

## 설정

### 환경 변수 (.env)

\`\`\`dotenv
# PostgreSQL
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=tuum_db
DATABASE_URL=postgresql://user:password@db:5432/tuum_db

# JWT
SECRET_KEY=your-secret-key

# Email (SMTP)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-password

# Environment
ENVIRONMENT=local  # local | dev | prod
\`\`\`

## 실행

### Docker Compose (권장)

\`\`\`bash
make dev
\`\`\`

### 개발 서버

\`\`\`bash
poetry install
poetry run uvicorn app.main:app --reload
\`\`\`

### 워커 실행

\`\`\`bash
poetry run python -m app.worker_main
\`\`\`

## 프로젝트 구조

\`\`\`
.
├── app/
│   ├── main.py              # FastAPI 진입점
│   ├── worker_main.py       # 크롤링 워커
│   └── src/
│       ├── domain/
│       │   ├── hotdeal/     # 핫딜 도메인
│       │   ├── user/        # 사용자 도메인
│       │   ├── mail/        # 메일 도메인
│       │   └── admin/       # 관리자 도메인
│       ├── Infrastructure/
│       │   ├── crawling/    # 크롤러
│       │   └── mail/        # 이메일 발송
│       └── core/            # 공통 (인증, DB, 설정)
├── static/                  # 웹 프론트엔드
├── tests/                   # 테스트
└── alembic/                 # DB 마이그레이션
\`\`\`
```

---

## Phase 6: 정리 및 검증

### 6.1 불필요 파일 정리
```bash
rm -rf .opencode
rm -rf .claude
rm -rf .agent
rm -rf .sisyphus  # 이 계획 파일도 정리
```

### 6.2 검증
- [ ] `poetry install` 성공
- [ ] `poetry run python -c "import app.main"` 성공
- [ ] LSP diagnostics 클린

---

## 체크리스트 요약

### 삭제 대상
- [x] `app/src/llm/` (디렉토리)
- [x] `app/src/clients/` (디렉토리)
- [x] `app/src/models/message.py`
- [x] `app/src/models/message_list.py`
- [x] `exmaple.py`
- [x] `static/chat.html`

### 수정 대상
- [x] `pyproject.toml` - 이름, 의존성
- [x] `app/main.py` - chat 라우트 제거
- [x] `.env.example` - LLM 키 제거
- [x] `README.md` - 전체 재작성

### 커밋/푸시
- **금지** (사용자 지시)

---

## 실행 명령어 (작업자용)

```bash
# 1. 복사 및 이동
NEW_NAME="tuum-day"  # 사용자 확인 필요
cp -r ~/dev/llm-chat-client ~/dev/$NEW_NAME
cd ~/dev/$NEW_NAME

# 2. Git 초기화
rm -rf .git
git init

# 3. LLM 관련 파일 삭제
rm -rf app/src/llm
rm -rf app/src/clients
rm app/src/models/message.py
rm app/src/models/message_list.py
rm exmaple.py
rm static/chat.html

# 4. 설정 파일 수정 (Edit tool 사용)
# - pyproject.toml
# - app/main.py
# - .env.example

# 5. README.md 재작성

# 6. 검증
poetry install
poetry run python -c "import app.main"
```
