# Plan: Update CI/CD Documentation (Cloudflare Pages Prerequisites)

## Context
The deployment failed because the Cloudflare Pages project `tuum-hotdeal` did not exist. The user had to create it manually. This step was missing from `docs/CICD.md`.

## Objectives
1.  **Update `docs/CICD.md`**: Add explicit instructions to create the Cloudflare Pages project *before* the first deployment.
2.  **Clarify "Direct Upload"**: Specify that the project type must be "Direct Upload" (not Connect to Git), as GitHub Actions handles the upload.
3.  **Troubleshooting**: Add a section for common errors (like 404 Project Not Found).

## Execution Steps

### 1. Edit `docs/CICD.md`
- [ ] Add a **"Prerequisites"** section under "Frontend Deployment".
- [ ] Document: Create Cloudflare Pages project.
  - Name: `tuum-hotdeal`
  - Source: **Direct Upload** (Critical!)
- [ ] Document: Get Account ID and API Token.
- [ ] Document: Add secrets to Doppler.

### 2. Commit and Push
- [ ] Commit message: `docs: add cloudflare pages project creation prerequisite to CICD guide`
- [ ] Push to `origin main`.

## Verification
- [ ] Verify `docs/CICD.md` contains the new prerequisite section.
- [ ] Verify changes are pushed to remote.
