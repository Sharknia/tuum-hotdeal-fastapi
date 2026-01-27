# Draft: Migration Plan - Frontend/Backend Separation

## Requirements
- **Frontend**: Move to Cloudflare Pages (`hotdeal.tuum.day`).
- **Backend**: Stay on VPS but change domain to `hotdeal-api.tuum.day`.
- **Code Changes**:
  - Frontend: Point API calls to `https://hotdeal-api.tuum.day`.
  - Backend: Allow CORS from `https://hotdeal.tuum.day`.
- **Infra Changes**:
  - Rename Nginx `server_name` from `hotdeal.tuum.day` to `hotdeal-api.tuum.day`.

## Exploration Results
- [Pending]

## Execution Steps
1. **Backend Code**: Update `app/main.py` or env vars for CORS.
2. **Frontend Code**: Update JS files to use the new API base URL.
3. **Nginx Config**: Update `server_name` and reload.
4. **Verification**: Test cross-origin requests.
