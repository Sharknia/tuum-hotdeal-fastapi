# CI/CD & Architecture Documentation

## Context

### Original Request
Analyze the current CI/CD setup (GitHub Actions -> Docker -> Nginx/Server) and create:
1.  Detailed documentation in `/docs`
2.  Summary documentation in `AGENT.md`

### Interview Summary
**Key Findings**:
- **CI/CD**: GitHub Actions workflow (`deploy.yml`) handles linting, testing, building (ARM64), and SSH deployment.
- **Runtime**: Docker Compose (`api` & `worker` containers) with Doppler for secrets.
- **Frontend**: Nginx used as reverse proxy (config external).
- **Static Files**: Application disables static serving in production; pipeline does NOT copy static files to host. This is a documented gap.
- **Architecture**: Target platform is `linux/arm64`.

### Metis Review
**Identified Gaps**:
- `DEPLOYMENT_SETUP.md` referenced in README is missing.
- Static file serving strategy is risky/manual.
- Platform specificity (`linux/arm64`) needs documentation.

---

## Work Objectives

### Core Objective
Create accurate documentation for the existing CI/CD pipeline and deployment architecture.

### Concrete Deliverables
- `docs/CICD.md` (Detailed technical documentation)
- `AGENT.md` (Concise AI context summary)

### Definition of Done
- [x] `docs/CICD.md` created with accurate steps and diagrams/descriptions.
- [x] `AGENT.md` created with key architecture points.
- [x] Both files accurate against the codebase state.

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: Yes (for app), but this is a docs task.
- **User wants tests**: N/A (Documentation only).
- **QA approach**: Manual verification of file content.

### Manual QA Only
Each TODO includes verification to check file existence and content.

---

## TODOs

- [x] 1. Create `docs/CICD.md`
  **What to do**:
  - Document the full pipeline:
    - **Lint/Test**: `poetry run ruff`, `poetry run pytest`
    - **Build**: Docker buildx (ARM64), Push to GHCR
    - **Deploy**: SSH, `docker compose pull && up -d`
  - Document the architecture:
    - Nginx (Reverse Proxy) -> Docker (Port 10000)
    - Doppler Secret Injection
    - External DB connection
  - **Important**: Add a "Known Limitations" section noting the Static Files issue (not copied to host, disabled in app prod mode) and ARM64 requirement.
  
  **References**:
  - `.github/workflows/deploy.yml`: Source of truth for pipeline.
  - `docker-compose.prod.yml`: Source of truth for runtime.
  - `README.md`: Existing (partial) docs.
  
  **Acceptance Criteria**:
  - [x] File exists: `docs/CICD.md`
  - [x] Contains "Pipeline Stages" section
  - [x] Contains "Infrastructure" section
  - [x] Mentions "Doppler" and "ARM64"
  - [x] Notes the "Static Files" limitation

- [x] 2. Create `AGENT.md`
  **What to do**:
  - Create a high-level summary for AI agents.
  - **CRITICAL**: The first line MUST be: `> **Always respond in Korean**`
  - The rest of the file content must be in **English**.
  - Structure:
    - **Instruction**: "Always respond in Korean" (at the very top)
    - **Project Identity**: Tech stack summary.
    - **CI/CD Summary**: "Push to main -> GH Action -> Deploy".
    - **Key Locations**: Where to find config files.
    - **Commands**: How to run/deploy manually (e.g., `make dev`).
  
  **References**:
  - `docs/CICD.md`: Summarize from here.
  
  **Acceptance Criteria**:
  - [x] File exists: `AGENT.md` (in root)
  - [x] First line is `> **Always respond in Korean**`
  - [x] File content is in English
  - [x] Concise (< 50 lines)
  - [x] Accurate summary of architecture

---

## Success Criteria

### Final Checklist
- [x] `docs/CICD.md` exists and is detailed.
- [x] `AGENT.md` exists and is concise.
- [x] Known limitations (static files, arm64) are documented.
