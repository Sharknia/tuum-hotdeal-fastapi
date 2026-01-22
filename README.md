# tuum.day - 핫딜 알림 서비스

사용자가 관심 키워드를 등록하면, 핫딜 사이트를 주기적으로 크롤링하여 새로운 핫딜 발견 시 이메일로 알림을 보내주는 서비스입니다.

## 주요 기능

- **사용자 인증**: 회원가입/로그인 (JWT 기반)
- **핫딜 키워드 관리**: 관심 키워드 등록/삭제
- **자동 크롤링**: 알구몬(algumon.com) 핫딜 사이트 30분 주기 크롤링
- **이메일 알림**: 새 핫딜 발견 시 구독자에게 이메일 발송
- **백그라운드 워커**: APScheduler 기반 스케줄링

## 기술 스택

| 분류 | 기술 |
|------|------|
| **Backend** | FastAPI, SQLAlchemy, PostgreSQL |
| **Worker** | APScheduler, asyncio |
| **Crawling** | BeautifulSoup, httpx |
| **Email** | aiosmtplib |
| **Auth** | JWT (python-jose), bcrypt |
| **Frontend** | Vanilla HTML/CSS/JS |
| **Infra** | Docker, Docker Compose |

## 설정

### 1. 저장소 클론

```bash
git clone https://github.com/Sharknia/tuum-hotdeal-fastapi.git
cd tuum-hotdeal-fastapi
```

### 2. Poetry 설치

```bash
pip install poetry
```

### 3. 의존성 설치

```bash
poetry install
```

### 4. 환경 변수 설정

프로젝트 루트에 `.env` 파일을 생성하고 다음 환경 변수들을 설정합니다.

```dotenv
# PostgreSQL 설정
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_DB=tuum_db

# FastAPI에서 사용할 DB URL
DATABASE_URL=postgresql://user:password@db:5432/tuum_db

# JWT 비밀 키
PASSWORD_SECRET_KEY=your-password-secret-key
EMAIL_SECRET_KEY=your-email-secret-key
REFRESH_TOKEN_SECRET_KEY=your-refresh-token-secret-key

# 환경 설정
ENVIRONMENT=local  # local | dev | prod
DEBUG=True

# SMTP 설정 (이메일 발송용)
SMTP_SERVER=smtp.example.com
SMTP_PORT=465
SMTP_EMAIL=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM=noreply@example.com
```

## 사용법

### Docker Compose를 사용한 개발 환경 실행 (권장)

```bash
make dev
```

또는 직접 Docker Compose 명령어 사용:

```bash
docker compose up --build
```

애플리케이션은 `http://localhost:8001`에서 접근 가능합니다.

### FastAPI 서버 직접 실행 (개발용)

```bash
poetry run uvicorn app.main:app --reload
```

또는:

```bash
make run
```

### 워커 실행 (크롤링 스케줄러)

```bash
poetry run python -m app.worker_main
```

## 프로젝트 구조

```
.
├── app/
│   ├── main.py              # FastAPI 진입점
│   ├── worker_main.py       # 크롤링 워커 (30분 주기)
│   └── src/
│       ├── domain/
│       │   ├── hotdeal/     # 핫딜 도메인 (models, services, routers)
│       │   ├── user/        # 사용자 도메인 (인증, JWT)
│       │   ├── mail/        # 메일 도메인
│       │   └── admin/       # 관리자 도메인
│       ├── Infrastructure/
│       │   ├── crawling/    # 크롤러 (알구몬)
│       │   └── mail/        # 이메일 발송
│       └── core/            # 공통 (인증, DB, 설정, 예외)
├── static/                  # 웹 프론트엔드 (HTML/CSS/JS)
├── tests/                   # 테스트 코드
├── alembic/                 # DB 마이그레이션
├── Dockerfile               # API 서버용
├── Dockerfile.worker        # 워커용
└── docker-compose.yml       # 개발 환경 설정
```

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/user/signup` | 회원가입 |
| POST | `/api/user/login` | 로그인 |
| GET | `/api/hotdeal/keywords` | 키워드 목록 조회 |
| POST | `/api/hotdeal/keywords` | 키워드 등록 |
| DELETE | `/api/hotdeal/keywords/{id}` | 키워드 삭제 |

## 라이선스

MIT License
