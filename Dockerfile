FROM python:3.12-slim AS builder

ENV POETRY_VERSION=2.1.1
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION

COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false \
    && poetry install --only main --no-interaction --no-ansi --no-root

FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app

# 런타임 시스템 패키지 및 Doppler CLI 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    netcat-openbsd \
    gnupg \
    gpgv \
    && curl -Ls --tlsv1.2 --proto "=https" --retry 3 https://cli.doppler.com/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Builder 단계의 Python 의존성/실행 스크립트만 복사
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Playwright 브라우저 및 시스템 의존성 설치
RUN playwright install chromium && playwright install-deps chromium

COPY . /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["/app/entrypoint.sh", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
