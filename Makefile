# Docker 이미지 이름 설정 (원하는 이름으로 변경 가능)
IMAGE_NAME = crobat-server-image
CONTAINER_NAME = crobat-server-container
WORKER_IMAGE_NAME = crobat-worker-image
WORKER_CONTAINER_NAME = crobat-worker-container

# Docker Compose 로 개발 환경 실행
dev:
	@echo "Cleaning up dangling images..."
	docker image prune -f
	@echo "Starting services with Docker Compose..."
	@echo "Ensure .env file is created and configured."
	docker compose up --build

example:
	poetry run python exmaple.py

# --- Docker 관련 명령어 추가 ---
docker-build:
	@echo "Building Docker image for main application..."
	docker build -t $(IMAGE_NAME) .

docker-run:
	@echo "Running Docker container for main application..."
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	docker run -d --name $(CONTAINER_NAME) -p 8000:8000 --env-file .env $(IMAGE_NAME)

docker-stop:
	@echo "Stopping Docker container for main application..."
	docker stop $(CONTAINER_NAME)

docker-logs:
	@echo "Showing Docker container logs for main application..."
	docker logs -f $(CONTAINER_NAME)

docker-clean:
	@echo "Removing Docker container for main application..."
	@docker stop $(CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(CONTAINER_NAME) 2>/dev/null || true
	@echo "Removing Docker image for main application..."
	docker rmi $(IMAGE_NAME) 2>/dev/null || true

# --- Worker Docker 관련 명령어 추가 ---
docker-build-worker:
	@echo "Building Docker image for worker..."
	docker build -f Dockerfile.worker -t $(WORKER_IMAGE_NAME) .

docker-run-worker:
	@echo "Running Docker container for worker..."
	@docker stop $(WORKER_CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(WORKER_CONTAINER_NAME) 2>/dev/null || true
	# 워커는 일반적으로 포트를 노출하지 않지만, 필요하다면 -p 옵션 추가
	# 동일한 .env 파일을 사용한다고 가정
	docker run -d --name $(WORKER_CONTAINER_NAME) --env-file .env $(WORKER_IMAGE_NAME)

docker-stop-worker:
	@echo "Stopping Docker container for worker..."
	docker stop $(WORKER_CONTAINER_NAME)

docker-logs-worker:
	@echo "Showing Docker container logs for worker..."
	docker logs -f $(WORKER_CONTAINER_NAME)

docker-clean-worker:
	@echo "Removing Docker container for worker..."
	@docker stop $(WORKER_CONTAINER_NAME) 2>/dev/null || true
	@docker rm $(WORKER_CONTAINER_NAME) 2>/dev/null || true
	@echo "Removing Docker image for worker..."
	docker rmi $(WORKER_IMAGE_NAME) 2>/dev/null || true

.PHONY: dev example docker-build docker-run docker-stop docker-logs docker-clean makemigrations docker-build-worker docker-run-worker docker-stop-worker docker-logs-worker docker-clean-worker

makemigrations:
	@docker compose exec web alembic revision --autogenerate -m "$(M)"

start-hotdeal-worker shw:
	PYTHONPATH=. poetry run python ./app/worker_main.py