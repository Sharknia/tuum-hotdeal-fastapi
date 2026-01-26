# Plan: Multi-Anchor Strategy (Robust Deleted Post Handling)

## Context
The current logic relies on a single "Anchor ID" to identify new posts. If this anchor post is deleted from the target site, the system fails to find the reference point and mistakenly treats the entire page as "New", causing a flood of old data emails.
The goal is to implement a **Multi-Anchor** strategy, storing the top 3 IDs (CSV format) instead of just 1. This ensures that if the top post is deleted, the system can fallback to the 2nd or 3rd post as the reference point.

## Objectives
1.  **Robustness**: Tolerate deletion of up to 2 top posts without losing context.
2.  **Universal Compatibility**: Works for any ID type (Numeric, String, UUID) without relying on comparison logic (magnitude).
3.  **Backward Compatibility**: Handle existing single-ID entries gracefully.

## Logic Change
In `app/worker_main.py`: `get_new_hotdeal_keywords_for_site`

**Logic**:
1.  **Read**: `anchors = last_crawled_site.external_id.split(",")`
2.  **Search**: Iterate through `anchors`.
    - Try to find `anchor` in `latest_products`.
    - If found at `index`:
        - `new_deals = latest_products[:index]` (All items *above* this anchor are new).
        - Break loop.
3.  **Fallback**: If loop finishes and NO anchor is found:
    - Assume **Massive New** (or massive deletion > 3).
    - `new_deals = latest_products` (Fetch All).
    - Log warning.
4.  **Write**: `new_anchors = [p.id for p in latest_products[:3]]`
    - `last_crawled_site.external_id = ",".join(new_anchors)`

## Verification Strategy
-   **Unit Test**: `tests/worker/test_multi_anchor.py`
    -   Case 1: **Legacy**: Saved "100". Found "100". Result: Empty.
    -   Case 2: **Normal**: Saved "100,99,98". Found "100". Result: Empty.
    -   Case 3: **New Item**: Saved "100,99,98". List "101,100...". Found "100". Result: "101".
    -   Case 4: **Deletion (1)**: Saved "100,99,98". List "101,99...". "100" missing. Found "99". Result: "101".
    -   Case 5: **Deletion (2)**: Saved "100,99,98". List "101,98...". Found "98". Result: "101".
    -   Case 6: **All Missing**: Saved "100,99,98". List "105,104...". Found None. Result: All.

---

## Task Flow
1. Create Test → 2. Implement Logic → 3. Verify

## TODOs

- [ ] 1. Create `tests/worker/test_multi_anchor.py`
    - **What to do**:
        - Implement the test cases described above.
        - Mock `get_crawler`, `session`, etc.
    - **Acceptance Criteria**:
        - Tests cover legacy single ID and new CSV format.

- [ ] 2. Modify `app/worker_main.py`
    - **What to do**:
        - Refactor `get_new_hotdeal_keywords_for_site`.
        - Implement CSV split/join logic.
        - Implement multi-anchor search loop.
    - **Acceptance Criteria**:
        - Code handles `ValueError` (not found) for individual anchors gracefully and continues to next.

- [ ] 3. Run Tests
    - **What to do**:
        - `pytest tests/worker/test_multi_anchor.py`
    - **Acceptance Criteria**:
        - All tests pass.

## Success Criteria
- [ ] Deletion of Top 1 post does NOT trigger "Fetch All".
- [ ] Deletion of Top 1 post CORRECTLY identifies new items above Top 2.
