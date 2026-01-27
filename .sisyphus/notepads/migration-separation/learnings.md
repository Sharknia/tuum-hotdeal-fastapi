# Learnings from Migration Separation

## Frontend Structure
- `static/js/auth.js` defines global authentication functions and `API_URL`. It is not an ES module.
- `static/script.js` was using ES module `import` syntax which failed because `auth.js` doesn't export anything.
- `static/js/keyword_manager.js` relies on `API_URL` being globally available.

## Deployment Architecture
- Frontend: Cloudflare Pages (`hotdeal.tuum.day`)
- Backend: VPS (`hotdeal-api.tuum.day`)
- This requires strict CORS configuration on the backend.
- Nginx on VPS must handle the `hotdeal-api.tuum.day` domain and proxy `/api` and `/ws` to localhost.
