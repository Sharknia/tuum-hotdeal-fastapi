> **[CRITICAL] RESPONSE LANGUAGE: KOREAN (한국어)**
> **모든 응답, 분석, 제안, 요약은 반드시 '한국어'로 작성하십시오.**
> **영어는 코드, 파일명, 로그, 기술 고유명사(Docker, FastAPI 등)에만 사용해야 합니다.**
> **사용자가 영어로 질문하더라도 한국어로 답변하십시오.**

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

- Test: `poetry run pytest`
- Lint: `poetry run ruff check .`

<available_skills>
<skill>
<name>feature-planner</name>
<description>(project - Skill) Creates phase-based feature plans with quality gates and incremental delivery structure. Use when planning features, organizing work, breaking down tasks, creating roadmaps, or structuring development strategy. Keywords: plan, planning, phases, breakdown, strategy, roadmap, organize, structure, outline.</description>
</skill>
<skill>
<name>commit-expert</name>
<description>(project - Skill) (opencode - Skill) 스마트 커밋 도우미. Conventional Commits 규칙 준수(한글, 개조식, 이모지 금지) 및 main 브랜치 보호 기능을 제공합니다. 커밋 메시지 작성, 브랜치 관리, 자동 스테이징 로직을 포함합니다. "커밋해줘", "commit", "변경사항 저장" 등의 요청 시 사용합니다.</description>
</skill>
<skill>
<name>skill-creator</name>
<description>(opencode-project - Skill) Guide for creating effective skills. This skill should be used when users want to create a new skill (or update an existing skill) that extends Claude's capabilities with specialized knowledge, workflows, or tool integrations.</description>
</skill>
<skill>
<name>deploy-expert</name>
<description>(project - Skill) 안전한 배포 프로세스 담당. 기능 브랜치 검증(Lint/Test), Main 병합(--no-ff), Push 및 브랜치 정리를 수행합니다. '배포해줘', 'deploy' 명령 시 사용합니다.</description>
</skill>
</available_skills>
