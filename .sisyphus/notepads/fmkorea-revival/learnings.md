# Learnings: Fmkorea Revival

## Test Dependencies
We found that `tests/infrastructure/test_crawler_registry.py` had a hardcoded assertion explicitly ensuring `FMKOREA` was *not* in the registry.
When re-enabling features, always search for tests that might enforce the "disabled" state.

## Crawler Logic
`FmkoreaCrawler` logic (parsing, URL extraction) proved to be robust enough to pass unit tests with mocked HTML based on the current implementation assumptions.
If the live site structure has changed, these tests will still pass (because they use mock HTML), but the crawler will fail in production.
Future work should involve "Live Verification" or "Contract Tests" that fetch real pages (if allowed/safe) to verify selectors match reality.
