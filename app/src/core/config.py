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
