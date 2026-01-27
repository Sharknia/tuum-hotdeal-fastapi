# Learnings from Admin Dashboard Fix

## Schema Mismatches
- **UserResponse**: Lacked `created_at`. Frontend expects it for join date.
- **KeywordResponse**: Lacked `wdate`. Frontend expects it for registration date.
- **WorkerLogResponse**: Backend uses `status` (Enum), Frontend expected `level` (String).
  - Resolved by aligning Frontend to use `status` and `details`.

## Frontend Logic
- **Admin JS**: Had a critical copy-paste error (duplicate function and IIFE closure) causing syntax error.
- **Keyword Table**: `user_id` column was removed because `Keyword` <-> `User` is a Many-to-Many relationship, and showing a single user ID is misleading or requires complex logic to show all.

## Testing
- Adding fields to Pydantic schemas can break tests that manually instantiate those models without the new fields.
- Always check usages of a schema in tests when modifying it.
