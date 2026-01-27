# Analysis: CI/CD Documentation vs Reality

## Current Documentation (Hypothesis)
- `README.md`: Likely describes the old monolithic Docker deployment.
- `docs/`: Might contain outdated guides.

## Actual Implementation (Hypothesis)
- Backend: GitHub Actions -> Build Docker -> Push GHCR -> SSH Deploy (Watchtower/Pull).
- Frontend: Cloudflare Pages (implied by user context, need to check if there is a workflow or if it's automatic via Cloudflare integration).

## Gap Analysis
- [Pending Search Results]
