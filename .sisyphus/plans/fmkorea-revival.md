# Plan: Re-enable Fmkorea Crawler

## Context
`FmkoreaCrawler` exists but is disabled (not registered). The recent refactoring of `SharedBrowser` makes it safe to re-enable it without causing memory leaks.
The goal is to re-enable it using TDD.

## Objectives
1.  **TDD**: Create comprehensive unit tests for `FmkoreaCrawler`.
2.  **Registration**: Add `FmkoreaCrawler` to the global registry and metadata.
3.  **Verification**: Ensure it integrates correctly with the new `SharedBrowser`.

## Verification Strategy
-   **Unit Tests**:
    -   `test_fmkorea_crawler.py`:
        -   Test `parse()` with mocked HTML (fixture).
        -   Test `_extract_post_id` with various URL formats.
        -   Test `_extract_price` and `_extract_meta_data`.
-   **Integration Test**:
    -   Verify `get_crawler(SiteName.FMKOREA)` returns a `FmkoreaCrawler` instance.

---

## Task Flow
1. Create Test File → 2. Register Crawler → 3. Verify

## TODOs

- [x] 1. Create `tests/infrastructure/test_fmkorea_crawler.py`
    - **What to do**:
        - Define `sample_fmkorea_html` fixture (mocking `.fm_best_widget .li` structure).
        - Test `parse()` returns correct `CrawledKeyword` list.
        - Test `_extract_post_id` logic.
    - **Acceptance Criteria**:
        - `pytest tests/infrastructure/test_fmkorea_crawler.py` FAILS initially (Red) or Passes if logic is correct but fails integration.
        - Actually, since the class exists, unit tests on the class *should* pass if the class logic is correct.
        - But `test_crawler_registry` might fail if we check for FMKOREA.

- [x] 2. Update `app/src/Infrastructure/crawling/crawlers/__init__.py`
    - **What to do**:
        - Import `FmkoreaCrawler`.
        - Add `SiteName.FMKOREA: FmkoreaCrawler` to `CRAWLER_REGISTRY`.
        - Add metadata to `SITE_METADATA`:
            - `display_name`: "에펨코리아"
            - `search_url_template`: `https://www.fmkorea.com/search.php?mid=hotdeal&search_keyword={keyword}&search_target=title_content`
    - **Acceptance Criteria**:
        - `get_crawler(SiteName.FMKOREA, ...)` works.

- [x] 3. Run All Tests
    - **What to do**:
        - Run `pytest tests/infrastructure/`.
    - **Acceptance Criteria**:
        - All tests pass, including `test_fmkorea_crawler.py`.

## Success Criteria
- [x] `FmkoreaCrawler` is active.
- [x] Unit tests cover parsing logic.
