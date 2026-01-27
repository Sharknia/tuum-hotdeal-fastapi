- Use DateTime(timezone=True) for consistency with created_at/updated_at.
- UserResponse is Pydantic v2, ensure nullable fields use 'datetime | None = None' for compatibility.
- In production-like environments without volume mapping (using images from GHCR), use 'docker cp' to sync local changes to the container before running migrations.
- Verify column existence with 'psql' using the correct database name and user found in environment variables (tuum_hotdeal / tuum).
## Alembic Migration Recovery
- Successfully generated migration ee0ff615f794 for last_login column.
- Applied migration to the database.
- Committed domain changes and migration separately for atomicity.
