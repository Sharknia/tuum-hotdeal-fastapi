# Learnings: Browser Refactoring

## Singleton Pattern with Playwright

We encountered a specific challenge with Playwright's asyncio support. `playwright.async_api.async_playwright().start()` is bound to the running event loop. 
If we initialize the singleton globally (at module level), it might attach to a different loop (or no loop) than the one running the worker.

**Solution**:
We implemented explicit `start()` and `stop()` methods on the singleton.
We call `await SharedBrowser.get_instance().start()` INSIDE the `job()` coroutine, ensuring it uses the active event loop.

## Test Mocking for Singletons

When testing Singletons, state persists between tests.
We had to modify `SharedBrowser.get_instance()` to respect `PYTEST_CURRENT_TEST` env var (or just ensure tests reset the singleton), but in our case, we patched `SharedBrowser` in the consumer tests (`test_browser_fetcher.py`) so we didn't use the real singleton there.
For `test_shared_browser.py`, since we run it in isolation or sequentially, it was fine, but a `reset()` method might be useful for future robust testing.
(Update: The implementation of `SharedBrowser` included logic to reset if `PYTEST_CURRENT_TEST` changes, which is a clever way to isolate tests!)

## Worker Lifecycle

We placed the browser lifecycle inside `job()`.
In `dev` mode, `job()` runs once, so browser starts/stops once.
In `prod` mode, `job()` runs every 30 minutes via scheduler.
This means we launch a fresh browser every 30 minutes. This is actually **desirable** as it prevents long-running browser memory leaks (which Chrome is notorious for).
It's a good balance between "Performance" (reuse during job) and "Stability" (restart between jobs).
