# Plan: Smart Anchor Recovery (Fix Old Data Flood)

## Context
When a stored "Anchor Post" (the last crawled ID) is deleted from the target site, the current logic fails to find it in the new list and falls back to fetching **all items** on the page. This causes a flood of old data emails.
The goal is to implement "Smart Anchor Recovery" that uses ID comparison to distinguish between "Newer items" and "Older items" when the anchor is missing.

## Objectives
1.  **Fix the Bug**: Stop sending old data when the anchor is deleted.
2.  **Support Massive New Posts**: If 20+ *new* posts appear, they should all be sent.
3.  **Safety**: Handle non-numeric IDs gracefully (Algumon risk) without crashing.

## Logic Change
In `app/worker_main.py`: `get_new_hotdeal_keywords_for_site`

**Current**:
```python
except ValueError:
    new_deals = latest_products  # Sends EVERYTHING
```

**New**:
```python
except ValueError:
    try:
        last_id = int(last_crawled_site.external_id)
        # Only keep items with ID > Last ID
        new_deals = [p for p in latest_products if p.id.isdigit() and int(p.id) > last_id]
    except ValueError:
        # Non-numeric fallback (Safe limit)
        new_deals = latest_products[:3]
```

## Verification Strategy
-   **Unit Test**: `tests/worker/test_smart_anchor.py`
    -   Test Case 1: **Deletion**. Saved=100. List=[99, 98]. Result=[].
    -   Test Case 2: **Massive New**. Saved=100. List=[120...101]. Result=[120...101].
    -   Test Case 3: **Mixed**. Saved=100. List=[102, 101, 99]. Result=[102, 101].
    -   Test Case 4: **Non-Numeric**. Saved="abc". List=["xyz", "abc"]. Result=Top 3.

---

## Task Flow
1. Create Test → 2. Implement Fix → 3. Verify

## TODOs

- [ ] 1. Create `tests/worker/test_smart_anchor.py`
    - **What to do**:
        - Use `get_new_hotdeal_keywords_for_site` logic (or mock it).
        - Since `get_new_hotdeal_keywords_for_site` is async and depends on DB/HTTP, we might extract the *filtering logic* or just test the function with mocks.
        - Better: Create a test that mocks `get_crawler`, `session`, etc., and calls `get_new_hotdeal_keywords_for_site`.
    - **Acceptance Criteria**:
        - Test fails (Red) or passes if logic matches (but we know current logic fails Deletion case).
        - Actually, current logic fails "Deletion" test (it returns all 99, 98).

- [ ] 2. Modify `app/worker_main.py`
    - **What to do**:
        - Locate `get_new_hotdeal_keywords_for_site`.
        - Replace `except ValueError` block with Smart Logic.
        - Ensure `int()` conversion is safe.
    - **Acceptance Criteria**:
        - Code handles numeric comparison correctly.

- [ ] 3. Run Tests
    - **What to do**:
        - `pytest tests/worker/test_smart_anchor.py`
    - **Acceptance Criteria**:
        - All tests pass.

## Success Criteria
- [ ] Deletion scenario returns 0 items.
- [ ] Massive New scenario returns all items.
