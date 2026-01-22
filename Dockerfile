# Python 3.12 Slim 이미지를 베이스로 사용합니다.
FROM python:3.12-slim

# 시스템 업데이트 및 빌드에 필요한 패키지 설치 (curl, build-essential 등)
RUN apt-get update && apt-get install -y curl build-essential netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Poetry 설치 (환경 변수 POETRY_VERSION을 통해 버전을 지정합니다. 여기서는 최신 안정 버전을 사용합니다.)
ENV POETRY_VERSION=2.1.1
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION

# Poetry 실행 파일이 위치한 경로를 환경 변수 PATH에 추가합니다.
ENV PATH="/root/.local/bin:$PATH"

# 작업 디렉터리를 /app으로 설정합니다.
WORKDIR /app

# pyproject.toml 및 poetry.lock 파일을 먼저 복사하여 의존성 설치 캐싱을 활용합니다.
COPY pyproject.toml poetry.lock* /app/

# Poetry 설정: 컨테이너 내에서는 별도의 가상환경 없이 시스템 환경을 사용하도록 설정합니다.
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

# 나머지 소스 코드 복사
COPY . /app

# Entrypoint 스크립트 복사 및 실행 권한 부여
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

WORKDIR /app

# Entrypoint 설정
ENTRYPOINT ["/app/entrypoint.sh"]

# 기본 실행 명령어 (Entrypoint가 실행할 명령어)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# FastAPI 기본 포트(8000) 노출 (기존 위치 또는 여기에 두어도 무방)
EXPOSE 8000
