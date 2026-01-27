# Decisions - Fix Admin Tabs

## 2026-01-27 - Merge Strategy Change
- **Initial Decision**: Push to feature branch only (requested by user).
- **Final Decision**: Merge to `main` with `--no-ff` (requested by user).
- **Rationale**: User wanted to preserve branch history in the main line.
- **Outcome**: Successfully merged `fix/admin-tabs-data-loading` into `main` with commit `ad63aa9`.
