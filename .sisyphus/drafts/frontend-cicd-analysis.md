# Draft: Frontend CI/CD Analysis (Finalized)

## Research Objectives
- [x] Identify CI/CD platform (GitHub Actions)
- [x] Locate frontend codebase (`static/`)
- [x] Analyze serving logic (FastAPI serves in local, Nginx serves in prod)
- [x] **CONFIRMED**: Nginx on host serves `/var/www/hotdeal`.

## The Setup (Dual-Mode)

### Local / Dev (Docker)
- FastAPI serves static files via `StaticFiles` mount.
- `app/main.py`: `if settings.ENVIRONMENT == "local": mount(...)`

### Production (VPS)
- **Nginx** handles static files.
- **Root**: `/var/www/hotdeal`
- **Proxy**: `/api/` -> `localhost:10000` (FastAPI)
- **FastAPI**: Runs with `ENVIRONMENT=prod` (so it disables its own static serving).

## The Missing Link
- How do files get from `static/` (repo) to `/var/www/hotdeal` (server)?
- The `.github/workflows/deploy.yml` builds a Docker image.
- **Does the deploy script copy files to `/var/www/hotdeal`?**
- **Hypothesis**: The deployment process is incomplete or manually done for static files? Or the deploy script does an `rsync`?

## Immediate Next Step
- Check `.github/workflows/deploy.yml` content to see if it copies static files to the server.
