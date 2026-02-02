# Remove Ruliweb Crawler

## TL;DR

> **Quick Summary**: Remove the Ruliweb crawler implementation and registry entry to stop redundancy (covered by Algumon), while preserving the `SiteName` Enum to maintain database integrity for historical data. This single change ensures removal from Crawler, API, and Frontend.
> 
> **Deliverables**:
> - Updated `crawlers/__init__.py` (Unregistered Ruliweb)
> - Deleted `ruliweb.py` (Implementation)
> - Deleted `test_ruliweb_crawler.py` (Tests)
> - Updated `test_site_info.py` (Refined assertions)
> 
> **Estimated Effort**: Quick
> **Parallel Execution**: Sequential
> **Critical Path**: Unregister → Delete Implementation → Verify

---

## Context

### Original Request
Remove Ruliweb crawling as it is duplicated by Algumon crawler. User explicitly requested removal from Frontend as well.

### Interview Summary
**Key Discussions**:
- Ruliweb is redundant; Algumon covers it.
- **CRITICAL DECISION**: `SiteName.RULIWEB` Enum MUST remain in `enums.py`. Removing it will break ORM deserialization for existing `KeywordSite` records in the database.
- **Frontend Removal**: Confirmed that `get_site_info_list` uses `CRAWLER_REGISTRY`, so removing from registry automatically clears it from API and Frontend.

### Metis Review
**Identified Gaps** (addressed):
- **Enum Safety**: Explicit guardrail added to keep `SiteName.RULIWEB`.
- **Registry vs Implementation**: Confirmed removing from `CRAWLER_REGISTRY` stops execution.
- **Hidden Dependencies**: Added `grep` check step to find unexpected usages.

---

## Work Objectives

### Core Objective
Stop Ruliweb crawling and clean up its code implementation without breaking existing data access. Ensure it disappears from Frontend UI.

### Concrete Deliverables
- [x] `app/src/Infrastructure/crawling/crawlers/__init__.py`: `SiteName.RULIWEB` removed from `CRAWLER_REGISTRY` and `SITE_METADATA`.
- [x] `app/src/Infrastructure/crawling/crawlers/ruliweb.py`: File deleted.
- [x] `tests/infrastructure/test_ruliweb_crawler.py`: File deleted.
- [x] `tests/infrastructure/test_site_info.py`: Assertions updated to not expect Ruliweb.

### Definition of Done
- [x] `pytest` passes 100%.
- [x] `get_active_sites()` does not return `ruliweb`.
- [x] `get_site_info_list()` does not return `ruliweb` (Verifies Frontend removal).
- [x] `SiteName.RULIWEB` still exists in codebase (verified via script).

### Must Have
- Clean removal of `ruliweb.py`.
- Preservation of `SiteName.RULIWEB` Enum.
- Removal from `CRAWLER_REGISTRY`.

### Must NOT Have (Guardrails)
- **DO NOT DELETE** `SiteName.RULIWEB` from `app/src/domain/hotdeal/enums.py`.
- **DO NOT DELETE** Alembic migrations related to Ruliweb.
- **DO NOT MODIFY** `algumon.py`.

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest)
- **User wants tests**: YES (Maintain green suite)
- **Framework**: pytest

### Verification Steps (Automated)

**Step 1: Enum Safety Check**
```bash
# Must print "ruliweb" without error
poetry run python -c "from app.src.domain.hotdeal.enums import SiteName; print(SiteName.RULIWEB.value)"
```

**Step 2: Registry & Frontend Check**
```bash
# Must NOT print "ruliweb"
poetry run python -c "from app.src.Infrastructure.crawling.crawlers import get_active_sites, get_site_info_list; print(f'Active: {[s.value for s in get_active_sites()]}'); print(f'API: {[s.name.value for s in get_site_info_list()]}')"
# Expected Output: Active: ['algumon', 'fmkorea'], API: ['algumon', 'fmkorea'] (NO ruliweb)
```

**Step 3: Full Suite**
```bash
poetry run pytest
```

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Sequential):
└── Task 1: Safe Removal & Cleanup
```

---

## TODOs

- [x] 1. Remove Ruliweb Crawler & Cleanup

  **What to do**:
  1.  **Safety Check**: Run `grep -r "Ruliweb" app/` to confirm no hidden dependencies exist.
  2.  **Unregister**: Edit `app/src/Infrastructure/crawling/crawlers/__init__.py`.
      - Remove `SiteName.RULIWEB` key from `CRAWLER_REGISTRY`.
      - Remove `SiteName.RULIWEB` key from `SITE_METADATA`.
      - Remove `from .ruliweb import RuliwebCrawler` import.
  3.  **Delete Tests**: Delete `tests/infrastructure/test_ruliweb_crawler.py`.
  4.  **Update Related Tests**: Edit `tests/infrastructure/test_site_info.py`.
      - Remove assertions that check for `SiteName.RULIWEB` presence in active lists.
      - Ensure test validates that `get_site_info_list()` returns ONLY registered sites.
  5.  **Delete Implementation**: Delete `app/src/Infrastructure/crawling/crawlers/ruliweb.py`.
  6.  **Verify**: Run the verification scripts defined below.

  **Must NOT do**:
  - Delete `SiteName.RULIWEB` from `enums.py`.
  - Delete migration files.

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward code removal and minor test updates.
  - **Skills**: [`python`]

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Sequential

  **References**:
  - `app/src/Infrastructure/crawling/crawlers/__init__.py`: Registry to modify.
  - `tests/infrastructure/test_site_info.py`: Test to update.

  **Acceptance Criteria**:

  **Automated Verification**:
  ```bash
  # 1. Enum Safety (Must output 'ruliweb')
  poetry run python -c "from app.src.domain.hotdeal.enums import SiteName; print(SiteName.RULIWEB.value)"

  # 2. Registry & Frontend Check (Must NOT contain 'ruliweb')
  poetry run python -c "from app.src.Infrastructure.crawling.crawlers import get_active_sites, get_site_info_list; sites=[s.name.value for s in get_site_info_list()]; print('ruliweb' in sites)"
  # Expected Output: False

  # 3. Test Suite
  poetry run pytest
  ```

  **Commit**: YES
  - Message: `refactor(crawler): remove ruliweb crawler`
  - Files: `app/src/Infrastructure/crawling/crawlers/__init__.py`, `tests/infrastructure/test_site_info.py` (and deleted files)

---

## Success Criteria

### Verification Commands
```bash
poetry run pytest
```

### Final Checklist
- [x] `ruliweb.py` is gone.
- [x] `test_ruliweb_crawler.py` is gone.
- [x] `__init__.py` is clean.
- [x] `enums.py` still has `RULIWEB`.
- [x] API does not return Ruliweb.
- [x] All tests pass.
