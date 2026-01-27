# Plan: Deploy Frontend to Cloudflare Pages

## Context
We are separating the frontend deployment from the monolithic backend container. The frontend (static HTML/CSS/JS) will be hosted on **Cloudflare Pages** for better performance (CDN), faster updates, and simpler management.

## Credentials
The user has added the following secrets to **Doppler**:
- `CLOUDFLARE_PAGES_API_TOKEN`
- `CLOUDFLARE_ACCOUNT_ID`

## Objectives
1.  **Modify CI/CD Pipeline**: Add a GitHub Actions job to deploy `static/` to Cloudflare Pages.
2.  **Secret Management**: Use `doppler-action` to fetch Cloudflare credentials during the build.
3.  **Documentation**: Update `docs/CICD.md` to reflect the new architecture.

## Execution Steps

### 1. Update `.github/workflows/deploy.yml`
- [x] Add a new job `deploy-frontend` that runs in parallel with `build`:

```yaml
  deploy-frontend:
    name: Deploy Frontend
    needs: [lint] # Can run parallel to backend build
    runs-on: ubuntu-latest
    permissions:
      contents: read
      deployments: write
    steps:
      - uses: actions/checkout@v4

      - name: Install Doppler CLI
        uses: dopplerhq/cli-action@v3

      - name: Fetch Secrets from Doppler
        uses: dopplerhq/secrets-fetch-action@v1.1.4
        id: doppler
        with:
          doppler-token: ${{ secrets.DOPPLER_TOKEN }}
          inject-env-vars: true

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/pages-action@v1
        with:
          apiToken: ${{ env.CLOUDFLARE_PAGES_API_TOKEN }}
          accountId: ${{ env.CLOUDFLARE_ACCOUNT_ID }}
          projectName: tuum-hotdeal
          directory: static
          gitHubToken: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Update `docs/CICD.md`
- [x] Describe the new split architecture.
- [x] Explain that Frontend -> Cloudflare Pages, Backend -> VPS (Docker).
- [x] Add a section on "Manual DNS Setup" for connecting the domain.

## Verification
- [ ] GitHub Action runs successfully (green check).
- [ ] Cloudflare Pages dashboard shows a new deployment.
- [ ] The deployed site loads correctly (e.g., `<project>.pages.dev`).

## Post-Deployment (User Action)
- User needs to configure Custom Domain in Cloudflare Dashboard to point `tuum.day` (or `www`) to the Pages project if desired, or keep using Nginx for main domain and verify.
