# Draft: Fix Admin Dashboard Plan

## Problem Analysis
- **User Issue**:
    1. Admin link not visible in header.
    2. Admin page data fetch failed.
    3. Tabs not working.
- **Root Cause Hypothesis**:
    1. **Serving**: `/admin` route in FastAPI is restricted to `local` env. In Prod, Nginx likely doesn't know how to serve `admin.html`.
    2. **JS Error**: If `admin.js` fails to load (404), tabs and fetch won't work.
    3. **Auth Logic**: `auth_level` check might still be failing or `userInfo` is not properly refreshed.

## Investigation Needed
- Check Nginx config: How is `/hotdeal` served? We need to replicate that for `/admin`.
- Check `admin.js`: Any obvious syntax errors?

## Proposed Strategy
1.  **Server Config**: Update Nginx to serve `/admin` -> `static/admin.html`.
2.  **Frontend Debugging**:
    - Fix `admin.js` if broken.
    - Verify `auth.js` logic with real browser test (Playwright).
3.  **Verification**:
    - Automated E2E test using Playwright.

## Next Steps
- Read Nginx config.
- Create detailed plan.
