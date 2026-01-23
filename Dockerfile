FROM python:3.12-slim

# 시스템 패키지 및 Doppler CLI 설치
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    netcat-openbsd \
    gnupg \
    && curl -Ls --tlsv1.2 --proto "=https" --retry 3 https://cli.doppler.com/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
ENV POETRY_VERSION=2.1.1
RUN curl -sSL https://install.python-poetry.org | python3 - --version $POETRY_VERSION
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
ENV PYTHONPATH=/app

COPY pyproject.toml poetry.lock* /app/
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root

# Playwright 브라우저 및 시스템 의존성 설치
RUN playwright install chromium && playwright install-deps chromium

COPY . /app

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

ENTRYPOINT ["doppler", "run", "--"]
CMD ["/app/entrypoint.sh", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
