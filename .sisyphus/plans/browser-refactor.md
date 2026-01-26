# Plan: Refactor BrowserFetcher to Singleton Pattern

## Context
The current `BrowserFetcher` implementation creates a new Playwright/Chromium instance for every single request. This causes resource exhaustion (RAM/CPU spikes) when multiple crawlers run in parallel.
The goal is to implement a Singleton pattern for the browser instance, sharing one browser process across all crawler tasks while maintaining isolation via BrowserContexts.

## Objectives
1.  **Stop the Fork Bomb**: Ensure only 1 Chromium instance is launched per worker process.
2.  **Maintain Isolation**: Continue using separate contexts/pages for each request.
3.  **TDD approach**: Write tests first to verify the lifecycle and singleton behavior.
4.  **Safe Lifecycle**: Ensure proper startup/shutdown within the asyncio event loop.

## Architecture Decisions
-   **New Class**: `SharedBrowser` (Singleton) in `app/src/Infrastructure/crawling/shared_browser.py`.
-   **Refactoring**: `BrowserFetcher` will no longer own the browser process; it will borrow it from `SharedBrowser`.
-   **Lifecycle**: `worker_main.py` will explicitly start `SharedBrowser` before the job loop and stop it after.
-   **Error Recovery**: `SharedBrowser` should handle browser crashes/disconnects by restarting if needed.

## Verification Strategy
-   **Unit Tests**:
    -   `test_shared_browser.py`: Verify singleton property (same instance returned) and start/stop behavior.
    -   `test_browser_fetcher.py`: Verify it calls `SharedBrowser` instead of launching new.
-   **Manual Verification**:
    -   Run worker locally, check `ps aux | grep chrome`. expected: 1 parent process.

---

## Task Flow
1. Create Test for SharedBrowser → 2. Implement SharedBrowser → 3. Update BrowserFetcher Tests → 4. Refactor BrowserFetcher → 5. Update Worker Lifecycle

## TODOs

- [x] 1. Create `tests/infrastructure/test_shared_browser.py`
    - **What to do**:
        - Write a test that instantiates `SharedBrowser`.
        - Verify calling `.start()` launches a browser (mocked).
        - Verify calling `.start()` twice returns the same instance.
        - Verify `.stop()` closes the browser.
    - **Acceptance Criteria**:
        - `pytest tests/infrastructure/test_shared_browser.py` fails (Red).

- [x] 2. Implement `SharedBrowser` Singleton
    - **What to do**:
        - Create `app/src/Infrastructure/crawling/shared_browser.py`.
        - Implement `SharedBrowser` class with `_instance`, `start()`, `stop()`, `get_browser()`.
        - Handle `async_playwright().start()` inside `start()`.
    - **Acceptance Criteria**:
        - `pytest tests/infrastructure/test_shared_browser.py` passes (Green).

- [x] 3. Update `tests/infrastructure/test_browser_fetcher.py`
    - **What to do**:
        - Remove tests that assert `BrowserFetcher` calls `playwright.start()`.
        - Add tests asserting `BrowserFetcher` calls `SharedBrowser.get_browser()`.
        - Update `test_close_cleans_up_browser` to *not* stop the global browser.
    - **Acceptance Criteria**:
        - Tests fail due to implementation mismatch (Red).

- [x] 4. Refactor `BrowserFetcher`
    - **What to do**:
        - Import `SharedBrowser`.
        - Remove `_playwright` and `_browser` instance variables.
        - In `_ensure_browser`, call `await SharedBrowser.get_instance().get_browser()`.
        - Remove `close()` logic that stops the browser (only cleanup context/page if needed).
    - **Acceptance Criteria**:
        - `pytest tests/infrastructure/test_browser_fetcher.py` passes (Green).

- [x] 5. Update `app/worker_main.py` Lifecycle
    - **What to do**:
        - Import `SharedBrowser`.
        - In `main()` (prod) and `job()` (dev wrapper), add:
            ```python
            await SharedBrowser.get_instance().start()
            try:
                # existing loop/job code
            finally:
                await SharedBrowser.get_instance().stop()
            ```
    - **Verification**:
        - Run `poetry run python -m app.worker_main` (dev mode).
        - Verify logs show browser start/stop.

## Success Criteria
- [x] All tests pass: `pytest tests/infrastructure/`
- [x] Worker starts without error.
- [x] `BrowserFetcher` no longer creates new browser processes.
