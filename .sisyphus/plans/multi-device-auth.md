# Multi-Device Auth Support Plan

## Context

### Objective
Enable users to stay logged in on multiple devices simultaneously (e.g., Phone and PC). Currently, logging in on a new device invalidates previous sessions (Single Session).

### Requirements
1.  **Multi-Device Support**: Switch from 1:1 to 1:N token relationship.
2.  **Device Info**: Display logged-in device details (Browser/OS) to the user.
3.  **Session Management**:
    -   View active sessions.
    -   Remote logout (specific device).
    -   "Logout from all other devices".
4.  **Session Limit**: Unlimited per user request, but implement a **soft limit of 50** to prevent abuse/performance issues.
5.  **Migration**: Active sessions must be preserved (migrated to new table).

### Technical Approach
-   **New Model**: `RefreshToken` table (1:N with User).
-   **Library**: `user-agents` for parsing User-Agent headers.
-   **Migration Strategy**:
    -   Step 1: Create `refresh_tokens` table.
    -   Step 2: Copy existing `User.refresh_token` values to new table (Data Migration).
    -   Step 3: Drop `User.refresh_token` column (or mark deprecated).
-   **Cleanup Strategy**:
    -   Trigger: On new login.
    -   Action: Delete expired tokens for that user.
    -   Action: If > 50 sessions, delete oldest.

---

## Verification Strategy

### Automated Tests (TDD)
-   **Model Tests**: Verify `RefreshToken` creation and relationship.
-   **Service Tests**:
    -   `login_user` creates new token row.
    -   `login_user` respects MAX_SESSIONS (deletes oldest if > 50).
    -   `refresh_access_token` updates existing row (rotation).
    -   `logout_user` deletes specific row.
    -   `logout_all` deletes all rows except current.
-   **Integration Tests**: Full flow (Login A -> Login B -> Both valid).

### Manual Verification
1.  **Login Flow**:
    -   Login on Chrome (Incognito 1) -> Success.
    -   Login on Firefox (Incognito 2) -> Success.
    -   Refresh token on Chrome -> Success (Firefox still valid).
2.  **Session List**:
    -   Call `GET /api/v1/users/sessions`.
    -   Verify correct Browser/OS info displayed for both.
3.  **Remote Logout**:
    -   Call `DELETE /api/v1/users/sessions/{id}` for Chrome.
    -   Verify Chrome refresh fails.
    -   Verify Firefox refresh succeeds.

---

## Task Flow

1.  **Setup**: Add dependencies.
2.  **Schema**: Create model & migration (with data copy).
3.  **Repo Layer**: Update DB operations.
4.  **Service Layer**: Implement logic & device parsing.
5.  **API Layer**: Update endpoints & add session management.
6.  **Cleanup**: Remove legacy column.

---

## TODOs

- [ ] 1. **Add Dependencies**
    -   **Action**: Add `user-agents` to `pyproject.toml`.
    -   **Command**: `poetry add user-agents`
    -   **Verify**: `poetry show user-agents`

- [ ] 2. **Create RefreshToken Model**
    -   **File**: `app/src/domain/user/models.py`
    -   **Action**: Define `class RefreshToken(Base)`:
        -   `id`: BigInteger, PK
        -   `user_id`: ForeignKey("users.id"), Index=True
        -   `token`: String(255), Index=True, Unique=True
        -   `user_agent`: String(512), Nullable=False (Default 'Unknown' if needed)
        -   `ip_address`: String(50), Nullable=True
        -   `created_at`: DateTime
        -   `updated_at`: DateTime
        -   `expires_at`: DateTime (Indexed for cleanup)
    -   **Action**: Add `refresh_tokens` relationship to `User` model.
    -   **Reference**: Follow existing `User` model patterns.

- [ ] 3. **Generate Database Migration (with Data Copy)**
    -   **Action**: Run Alembic to generate migration script.
    -   **Command**: `alembic revision --autogenerate -m "add_refresh_token_table"`
    -   **Edit Script**: Add data migration logic in `upgrade()`:
        ```python
        # Pseudo-code for data migration
        connection.execute(
            """
            INSERT INTO refresh_tokens (user_id, token, user_agent, ip_address, created_at, updated_at, expires_at)
            SELECT id, refresh_token, 'Legacy Session', NULL, NOW(), NOW(), NOW() + INTERVAL '7 days'
            FROM users
            WHERE refresh_token IS NOT NULL
            """
        )
        ```
    -   **Apply**: `alembic upgrade head`

- [ ] 4. **Update Repository Layer (Save/Create)**
    -   **File**: `app/src/domain/user/repositories.py`
    -   **Refactor**: `save_refresh_token`
    -   **Change**: Instead of `update(User)...`, use `insert(RefreshToken)...`.
    -   **Input**: Add `user_agent` (str) and `ip_address` (str | None) parameters.

- [ ] 5. **Update Repository Layer (Read/Verify)**
    -   **File**: `app/src/domain/user/repositories.py`
    -   **Refactor**: `get_refresh_token` / `verify_refresh_token`
    -   **Change**: Query `RefreshToken` table by token value.
    -   **Return**: Return `RefreshToken` object.

- [ ] 6. **Update Repository Layer (Delete/Logout)**
    -   **File**: `app/src/domain/user/repositories.py`
    -   **Refactor**: `delete_refresh_token`
    -   **Change**: `delete(RefreshToken).where(RefreshToken.token == token)`
    -   **New Function**: `delete_all_refresh_tokens(user_id)`
    -   **New Function**: `delete_refresh_token_by_id(session_id)`
    -   **New Function**: `cleanup_expired_tokens(user_id)`

- [ ] 7. **Update Service Layer (Login)**
    -   **File**: `app/src/domain/user/services.py`
    -   **Refactor**: `login_user`
    -   **Signature Change**: Update signature to accept device info:
        `async def login_user(..., user_agent: str, ip_address: str | None) -> ...`
    -   **Action**:
        -   **Cleanup**: Call `cleanup_expired_tokens`.
        -   **Limit Check**: If session count > 50, delete oldest.
        -   Pass info to `create_refresh_token` -> `save_refresh_token`.

- [ ] 8. **Update Service Layer (Refresh)**
    -   **File**: `app/src/domain/user/services.py`
    -   **Refactor**: `refresh_access_token`
    -   **Logic**:
        -   Find token row.
        -   Verify expiry.
        -   **Rotation**: Generate NEW token string using `jwt.encode`.
        -   **Update**: Update `token`, `expires_at`, `updated_at` in the *same row* (preserving ID/UA/IP).

- [ ] 9. **Implement Session Schemas & Service**
    -   **File**: `app/src/domain/user/schemas.py`
    -   **New Schema**: `SessionResponse`
        -   `id`: int
        -   `user_agent`: str
        -   `ip_address`: str | None
        -   `last_used`: datetime (map from updated_at)
        -   `created_at`: datetime
        -   `is_current`: bool (computed in router)
    -   **New Schema**: `SessionListResponse` -> `list[SessionResponse]`
    -   **File**: `app/src/domain/user/services.py`
    -   **New Function**: `get_active_sessions(user_id)`
    -   **New Function**: `logout_specific_session(session_id, user_id)`
    -   **New Function**: `logout_all_other_sessions(user_id, current_token)`

- [ ] 10. **Update API Endpoints**
    -   **File**: `app/src/domain/user/v1/router.py`
    -   **Action**: Update `login` signature:
        `async def login(request: Request, ...)`
    -   **Extraction**:
        -   `user_agent = request.headers.get("user-agent", "Unknown")`
        -   `ip_address = request.client.host if request.client else None`
    -   **Update**: `/token/refresh` (Handle rotation correctly).
    -   **New Endpoint**: `GET /sessions` -> `SessionListResponse`
    -   **New Endpoint**: `DELETE /sessions/{session_id}`
        -   **Error Handling**: Return 404 if not found or 403 if not owner.
        -   **Exceptions**: Create `SessionNotFound`, `SessionAccessDenied`.
    -   **New Endpoint**: `DELETE /sessions` (Logout all).

- [ ] 11. **Cleanup Legacy Column**
    -   **Action**: Create new migration to remove `refresh_token` column from `users` table.
    -   **Command**: `alembic revision --autogenerate -m "remove_user_refresh_token_column"`
    -   **Apply**: `alembic upgrade head`

- [ ] 12. **Final Verification**
    -   **Action**: Run full test suite.
    -   **Command**: `poetry run pytest`
    -   **Manual**: Verify multi-device login scenario.
