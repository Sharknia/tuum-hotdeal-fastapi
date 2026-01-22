# tuum.day - 핫딜 알림 서비스

> ⚠️ **학습 목적 프로젝트**  
> 이 프로젝트는 FastAPI, Docker, CI/CD 등 백엔드 기술 스택 학습을 위해 제작되었습니다.  
> 프로덕션 서비스가 아니며, 학습 및 참고 용도로만 사용해주세요.

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
| **Infra** | Docker, GitHub Actions, GHCR |
| **Secrets** | Doppler |

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
├── Dockerfile               # API 서버 및 워커 (통합 이미지)
└── docker-compose.yml       # 개발 환경 설정
```

## CI/CD

### 개요

`main` 브랜치에 push되면 GitHub Actions가 자동으로 테스트, 빌드, 배포를 수행합니다.

```
Push to main → Test → Build → Deploy → Tag
```

### 파이프라인 단계

| 단계 | 설명 |
|------|------|
| **Test** | Ruff 린트 + Pytest 테스트 실행 |
| **Build** | Docker 이미지 빌드 → GHCR에 푸시 |
| **Deploy** | SSH로 서버 접속 → 이미지 pull → 컨테이너 재시작 |
| **Tag** | `deploy-YYYYMMDD-SHA` 형식의 배포 태그 생성 |

### 시크릿 관리 (Doppler)

환경변수는 [Doppler](https://doppler.com)를 통해 관리됩니다. 서버에 `.env` 파일을 두지 않고, 컨테이너 실행 시 Doppler CLI가 런타임에 환경변수를 주입합니다.

```dockerfile
ENTRYPOINT ["doppler", "run", "--"]
CMD ["uvicorn", "app.main:app", ...]
```

**장점:**
- 서버에 시크릿 파일이 존재하지 않음
- 중앙 집중식 환경변수 관리
- 환경변수 변경 시 컨테이너 재시작만으로 반영

### 배포 환경

| 항목 | 값 |
|------|-----|
| **이미지 레지스트리** | `ghcr.io/sharknia/tuum-hotdeal-fastapi` |
| **서버 경로** | `~/app/tuum-hotdeal-fastapi` |
| **포트** | 10000 (nginx 리버스 프록시 연결) |

### 초기 설정

배포 환경 설정은 [`DEPLOYMENT_SETUP.md`](./DEPLOYMENT_SETUP.md)를 참조하세요.

## API 엔드포인트

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/user/signup` | 회원가입 |
| POST | `/api/user/login` | 로그인 |
| GET | `/api/hotdeal/keywords` | 키워드 목록 조회 |
| POST | `/api/hotdeal/keywords` | 키워드 등록 |
| DELETE | `/api/hotdeal/keywords/{id}` | 키워드 삭제 |
| GET | `/health` | 헬스체크 |

## 라이선스

MIT License
