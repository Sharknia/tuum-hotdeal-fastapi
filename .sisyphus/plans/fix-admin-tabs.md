# Fix Admin Page Tab Switching Issue

## Context

### Original Request
**User's Goal**: Fix the issue where data loading fails when switching tabs in the admin page (User Management / Keyword Management / System Log).
**Requirement**: Provide a plan that includes a branch strategy.

### Root Cause Analysis
- **Symptom**: Clicking tabs switches the active tab style, but the content section does not appear (or data appears not to load).
- **Technical Cause**: Mismatch between HTML IDs and JavaScript logic.
  - `static/js/admin.js` expects section IDs to be `{data-tab}-section`.
    - `data-tab="users"` → expects `users-section`
    - `data-tab="keywords"` → expects `keywords-section`
    - `data-tab="logs"` → expects `logs-section`
  - `static/admin.html` defines singular IDs:
    - `id="user-section"`
    - `id="keyword-section"`
    - `id="log-section"`
  - **Result**: JavaScript removes the `active` class from the previously visible section but fails to find the new section to add the `active` class to. The section remains hidden (`display: none`).

### Metis Review
- **Confirmed**: Diagnosis is correct.
- **Risk**: Browser/CDN caching of old HTML.
- **Recommendation**: Rename HTML IDs to plural to match JavaScript convention.

---

## Work Objectives

### Core Objective
Fix the tab switching logic by aligning HTML IDs with JavaScript expectations so that content sections correctly display when tabs are clicked.

### Concrete Deliverables
- Modified `static/admin.html` with renamed section IDs.

### Definition of Done
- [x] `static/admin.html` contains `id="users-section"`, `id="keywords-section"`, `id="logs-section"`.
- [x] No `id="user-section"`, `id="keyword-section"`, `id="log-section"` exist in the file.

### Must Have
- Fix must be done in HTML (not JS) to maintain cleaner "plural" convention for collections.

### Must NOT Have (Guardrails)
- Do NOT modify `static/js/admin.js` logic.
- Do NOT change `data-tab` values.
- Do NOT merge back to main (User explicitly requested push-to-feature-only).

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: Tests exist (pytest), but this is a pure frontend HTML fix.
- **User wants tests**: Manual verification is sufficient for this UI fix.
- **Framework**: Manual / Browser.

### Manual Execution Verification

**For Frontend/UI changes:**
- [x] **Verify File Content**:
    - Command: `grep -E "id=\"(users|keywords|logs)-section\"" static/admin.html`
    - Expected: Matches all 3 sections.
    - Command: `grep -E "id=\"(user|keyword|log)-section\"" static/admin.html`
    - Expected: No matches.

---

## Task Flow

```
1. Create Branch → 2. Rename HTML IDs → 3. Verify → 4. Push to Feature Branch
```

---

## Branch Strategy (User Requested)

The project follows a Feature Branch workflow based on `main` (Trunk-Based / GitHub Flow).
**NOTE:** User requested to stop after pushing the feature branch. Merging is excluded.

1.  **Base Branch**: `main` (Production)
2.  **Feature Branch**: `fix/admin-tabs-data-loading`
3.  **End State**: Feature branch pushed to origin (No Merge).

**Commands:**
```bash
git checkout main
git pull origin main
git checkout -b fix/admin-tabs-data-loading
# ... implement changes ...
git add static/admin.html
git commit -m "fix(frontend): align admin section IDs with js logic"
git push -u origin fix/admin-tabs-data-loading
```

---

## TODOs

- [x] 1. Fix HTML ID Mismatch in Admin Page

  **What to do**:
  - Open `static/admin.html`.
  - Find `<section id="user-section" ...>`. Rename to `users-section`.
  - Find `<section id="keyword-section" ...>`. Rename to `keywords-section`.
  - Find `<section id="log-section" ...>`. Rename to `logs-section`.

  **References**:
  - `static/admin.html:167` - User section definition.
  - `static/admin.html:189` - Keyword section definition.
  - `static/admin.html:209` - Log section definition.
  - `static/js/admin.js:13-17` - Logic deriving ID from `data-tab`.

  **Acceptance Criteria**:
  - [x] `grep "id=\"users-section\"" static/admin.html` returns match.
  - [x] `grep "id=\"keywords-section\"" static/admin.html` returns match.
  - [x] `grep "id=\"logs-section\"" static/admin.html` returns match.

  **Commit**: YES
  - Message: `fix(frontend): align admin section IDs with js logic`
  - Files: `static/admin.html`
  - Push: YES (to `origin fix/admin-tabs-data-loading`)

---

## Success Criteria

### Final Checklist
- [x] `static/admin.html` has correct plural IDs.
- [x] `static/js/admin.js` logic (which expects plural) works with the new HTML.
- [x] Changes are committed and pushed to `fix/admin-tabs-data-loading`.
