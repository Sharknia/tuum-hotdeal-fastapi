> **Always respond in Korean**

## Project Identity
- **Name**: Tuum Hotdeal Service
- **Stack**: FastAPI, Docker, Nginx, Doppler
- **Target Architecture**: ARM64

## CI/CD Pipeline Summary
The deployment is fully automated via GitHub Actions:
`Push to main` -> `Lint & Test` -> `Build (ARM64)` -> `Deploy (SSH/Compose)` -> `Tag`

1. **Lint/Test**: Performs code analysis with Ruff and runs tests with Pytest.
2. **Build**: Builds a Docker image for the `linux/arm64` platform.
3. **Deploy**: Deploys to the production server via SSH using Docker Compose.
4. **Tag**: Tags the successful deployment with a timestamp and commit SHA.

## Key Locations
- **Pipeline Configuration**: `.github/workflows/deploy.yml`
- **Runtime Configuration**: `docker-compose.prod.yml`
- **Detailed Docs**: `docs/CICD.md` (Source of truth for deployment architecture)

## Commands
- **Local Development**: `make dev` or `docker compose up`
- **Manual Deployment**: N/A (Automated via GitHub Actions)

## Verification Rule
After completing tasks, ALWAYS run full tests and linter checks to ensure the deployment pipeline will pass:
- Lint: `poetry run ruff check .`
- Test: `poetry run pytest`
