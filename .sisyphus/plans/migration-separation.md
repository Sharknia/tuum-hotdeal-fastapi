# Migration Plan: Frontend/Backend Separation

## Context
- **Goal**: Separate Frontend (Cloudflare Pages) and Backend (VPS).
- **Frontend URL**: `https://hotdeal.tuum.day`
- **Backend URL**: `https://hotdeal-api.tuum.day`
- **Current State**: Frontend code has hardcoded relative paths (`/api`) and incorrect imports. Backend CORS needs updating.

## Work Objectives
1.  Update Frontend code to use the new Backend URL in production.
2.  Update Backend code to allow CORS from the new Frontend URL.
3.  Document Nginx changes required on the VPS.

## Todo List

- [x] **Frontend: Update API Base URL**
    - **File**: `static/js/auth.js`
    - **Action**: In `getApiUrl`, change the `else` block (production) to return `'https://hotdeal-api.tuum.day/api'`.

- [x] **Frontend: Fix Keyword Manager Fetch**
    - **File**: `static/js/keyword_manager.js`
    - **Action**: In `loadSites`, change `fetch('/api/hotdeal/v1/sites')` to `fetch(\`\${API_URL}/hotdeal/v1/sites\`)`.

- [x] **Frontend: Fix Script.js**
    - **File**: `static/script.js`
    - **Action**:
        1. Comment out or remove `import ... from './js/auth_utils.js';`.
        2. Change `checkLoginStatus()` to `hasValidTokens()`.
        3. Change `wsUrl` to `'wss://hotdeal-api.tuum.day/ws'`.

- [x] **Backend: Update CORS**
    - **File**: `app/main.py`
    - **Action**: Add `"https://hotdeal.tuum.day"` to the `origins` list in the `prod` environment block.

- [x] **Documentation: Nginx Setup**
    - **File**: `docs/VPS_NGINX_SETUP.md`
    - **Action**: Create this file with the following content:
      ```markdown
      # VPS Nginx Setup Guide

      ## 1. Update Server Name
      Edit `/etc/nginx/sites-available/tuum.day`:

      ```nginx
      server {
          listen 80;
          server_name hotdeal-api.tuum.day;
          return 301 https://$host$request_uri;
      }

      server {
          listen 443 ssl;
          server_name hotdeal-api.tuum.day;
          
          # ... existing ssl config ...
          
          location /api/ {
              proxy_pass http://localhost:10000;
              # ...
          }
      }
      ```

      ## 2. Apply Changes
      Run: `sudo nginx -t && sudo systemctl reload nginx`
      ```

- [x] **Verification**
    - **Action**: Review changes and verify syntax.
    - **Manual Check**: User will deploy and test.

## Success Criteria
- Frontend code references `hotdeal-api.tuum.day` in production.
- Backend allows CORS from `hotdeal.tuum.day`.
- Nginx documentation is available.
