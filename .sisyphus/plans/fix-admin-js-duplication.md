# Fix Admin JS Duplication

## Context
Code review identified a duplication bug in `static/js/admin.js` where the `deleteKeyword` function and the closing IIFE block are repeated at the end of the file.

## Work Objectives
- Remove duplicated code block in `static/js/admin.js`.
- Ensure `deleteKeyword` function remains defined exactly once.
- Ensure IIFE properly closes.

## Todo List
- [ ] Remove lines 238-259 in `static/js/admin.js`.
- [ ] Verify file content ends with `})();`.
- [ ] Manual verification: Check if admin page loads without console errors.

## References
- `static/js/admin.js`: Lines 238-259 (Duplicate block)
