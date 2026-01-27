# Learnings - Fix Admin Tabs

## 2025-01-27 - HTML ID Mismatch Fix
- **Issue**: Admin page tabs weren't switching content because `admin.js` expected plural IDs (`users-section`) but HTML had singular (`user-section`).
- **Fix**: Renamed HTML IDs to match JS expectation (plural).
- **Strategy**: Modified `static/admin.html` instead of JS to maintain cleaner convention.
- **Verification**: Confirmed with `grep` that IDs match `users-section`, `keywords-section`, `logs-section`.
