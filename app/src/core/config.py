from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 데이터베이스 설정
    DATABASE_URL: str

    # LLM API 키
    GROK_API_KEY: str | None = None
    GOOGLE_API_KEY: str | None = None

    # JWT 비밀 키 (나중에 인증 추가 시 사용)
    SECRET_KEY: str = "a_very_secret_key_that_should_be_changed"
    REFRESH_TOKEN_SECRET_KEY: str
    EMAIL_SECRET_KEY: str
    PASSWORD_SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 개발/운영 환경 구분 (선택 사항)
    ENVIRONMENT: str = "local"
    DEBUG: bool = True

    # 메일링 관련 설정
    SMTP_SERVER: str = "smtp.kakao.com"
    SMTP_PORT: int = 465
    SMTP_EMAIL: str = "hotdeal@tuum.day"
    SMTP_PASSWORD: str = "hotdeal1234"
    SMTP_FROM: str = "hotdeal@tuum.day"

    # 크롤링 동시성/차단 대응 설정
    CRAWL_SITE_CONCURRENCY: int = 2
    CRAWL_KEYWORD_CONCURRENCY: int = 4
    CRAWL_SITE_CONCURRENCY_MAX: int = 4
    CRAWL_KEYWORD_CONCURRENCY_MAX: int = 8
    CRAWL_BLOCK_BACKOFF_SECONDS: float = 3.0
    CRAWL_BLOCK_BACKOFF_MAX_SECONDS: float = 60.0
    CRAWL_BLOCK_BACKOFF_BUDGET_SECONDS: float = 180.0
    CRAWL_SITE_BUDGET_SECONDS: float = 120.0
    WORKER_RUN_TIMEOUT_SECONDS: float = 1500.0
    WORKER_LOG_MONITOR_WINDOW_MINUTES: int = 90

    # 프록시 밴 정책/보강 설정
    MIN_AVAILABLE_PROXIES: int = 5
    PROXY_REPLENISH_ATTEMPTS: int = 2
    PROXY_FETCH_LIMIT: int = 15

    PROXY_SOFT_BAN_FAILURE_THRESHOLD: int = 2
    PROXY_SOFT_BAN_TTL_SECONDS: int = 900
    PROXY_HARD_BAN_FAILURE_THRESHOLD: int = 5
    PROXY_SUCCESS_DECAY: int = 1

    PROXY_BACKOFF_BLOCKED_SECONDS: float = 5.0
    PROXY_BACKOFF_NETWORK_SECONDS: float = 3.0
    PROXY_BACKOFF_SSL_SECONDS: float = 8.0
    PROXY_BACKOFF_SERVER_SECONDS: float = 4.0
    PROXY_BACKOFF_UNKNOWN_SECONDS: float = 2.0

    PROXY_HEALTHCHECK_ENABLED: bool = True
    PROXY_HEALTHCHECK_URL: str = "https://httpbin.org/ip"
    PROXY_HEALTHCHECK_TIMEOUT_SECONDS: float = 5.0
    PROXY_SOURCE_FAILURE_THRESHOLD: int = 3
    PROXY_SOURCE_COOLDOWN_SECONDS: int = 600

    CRAWL_PROTECTION_SITE_CONCURRENCY: int = 1
    CRAWL_PROTECTION_KEYWORD_CONCURRENCY: int = 2
    CRAWL_PROTECTION_KEYWORD_RATIO: float = 0.5

    model_config = SettingsConfigDict(
        # .env 파일 경로 명시 (기본값은 프로젝트 루트의 .env)
        env_file=".env",
        env_file_encoding="utf-8",
        # 환경 변수 이름에 접두사 추가 방지 (선택 사항)
        # env_prefix="APP_",
        # 대소문자 구분 (기본값 False)
        case_sensitive=False,
        # 클래스에 정의되지 않은 .env 변수 무시
        extra="ignore",
    )


# 설정 인스턴스 생성 (이 시점에 .env 파일 로드 시도, 무해한 주석 변경)
settings = Settings()
