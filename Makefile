# Docker 이미지 이름 설정
IMAGE_NAME = tuum-hotdeal-image
CONTAINER_NAME = tuum-hotdeal-container

# Docker Compose 로 개발 환경 실행
dev:
	@echo "Cleaning up dangling images..."
	docker image prune -f
	@echo "Starting services with Docker Compose..."
	@echo "Ensure .env file is created and configured."
	docker compose up --build

example:
	poetry run python example.py

# --- Docker 관련 명령어 ---
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

.PHONY: dev example docker-build docker-run docker-stop docker-logs docker-clean makemigrations start-hotdeal-worker shw

makemigrations:
	@docker compose exec web alembic revision --autogenerate -m "$(M)"

start-hotdeal-worker shw:
	PYTHONPATH=. poetry run python ./app/worker_main.py
