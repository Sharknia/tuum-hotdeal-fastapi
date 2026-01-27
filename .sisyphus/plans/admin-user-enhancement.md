# Admin Page User Management Enhancements

## Context

### Git Strategy (MANDATORY)
- **Feature Branch**: `feature/admin-user-enhancement`
- **Workflow**:
    1. Create branch: `git checkout -b feature/admin-user-enhancement`
    2. Commit changes incrementally.
    3. **Final Action**: Push to remote.
    4. **PROHIBITED**: Do NOT merge to main/master.
- **Push Command**: `git push -u origin feature/admin-user-enhancement`

### Original Request
Enhance the Admin Page User Management section with:
1. **Last Login Time**: Add column to user list.
2. **Approval Management**: Add "Approve" and "Unapprove" functionality.
3. **Detail View**: Add a detail page showing user info and monitored keywords.

### Analysis & Decisions
- **Last Login**: Currently missing from DB. Will add `last_login` column via Alembic migration and update it on login.
- **Unapprove Logic**: Mapped to `is_active = False` (inverse of existing Approve logic).
- **Keyword Display**: Read-only list in the detail view.
- **Frontend Architecture**: Multi-page static HTML. Will create new `admin_user_detail.html`.

---

## Work Objectives

### Core Objective
Implement full lifecycle user management in the admin panel, including activity tracking (last login), access control (approve/unapprove), and detailed monitoring insight (keywords).

### Concrete Deliverables
- **DB Migration**: Alembic script for `users.last_login`.
- **API Endpoints**:
    - `PATCH /admin/users/{id}/unapprove`
    - `GET /admin/users/{id}` (includes keywords)
- **Frontend Pages**:
    - Updated `static/admin.html` (Table columns, Actions)
    - New `static/admin_user_detail.html` (Detail view)

### Definition of Done
- [ ] `last_login` is updated in DB when a user logs in.
- [ ] Admin user list shows `last_login` timestamp.
- [ ] Admin can "Unapprove" a user, setting `is_active` to False.
- [ ] Clicking a user navigates to the detail page showing their keywords.

---

## Verification Strategy

### Test Infrastructure
- **Framework**: `pytest` exists in the project.
- **Strategy**: Manual Verification (Primary for Frontend) + API Tests (Recommended).
- **Frontend**: Manual verification via browser (using `static/` server).

### Manual QA Procedure
1. **Login Flow**:
    - Login as a normal user.
    - Check DB: `SELECT last_login FROM users WHERE email='...'` -> Should be updated.
2. **Admin List**:
    - Login as Admin.
    - Go to `/static/admin.html`.
    - Verify "Last Login" column exists and shows data.
3. **Approval Flow**:
    - Click "Unapprove" on a user.
    - Verify UI updates (User status changes).
    - Check DB: `SELECT is_active FROM users...` -> Should be `false`.
    - Click "Approve".
    - Verify UI updates.
4. **Detail Flow**:
    - Click on User's nickname.
    - Verify navigation to `/static/admin_user_detail.html?id=...`.
    - Verify user info matches.
    - Verify "Keywords" list is populated.

---

## TODOs

- [x] 1. **Database Migration**
    - **What to do**:
        - Create Alembic migration: `alembic revision --autogenerate -m "add_last_login_to_users"`
        - Verify `last_login` column (DateTime, nullable=True) is added to `users` table.
        - Apply migration: `alembic upgrade head`
    - **References**:
        - `app/src/domain/user/models.py`: Add field here first.
        - `alembic/`: Migration directory.
    - **Acceptance Criteria**:
        - [ ] `psql -c "\d users"` shows `last_login` column.

- [x] 2. **Update User Model & Schema**
    - **What to do**:
        - Update `User` model (`app/src/domain/user/models.py`) with `last_login`.
        - Update `UserResponse` schema (`app/src/domain/user/schemas.py`) to include `last_login: datetime | None`.
    - **References**:
        - `app/src/domain/user/models.py`
        - `app/src/domain/user/schemas.py`
    - **Acceptance Criteria**:
        - [ ] API documentation (Swagger) shows `last_login` in User response.

- [ ] 3. **Implement Last Login Logic**
    - **What to do**:
        - In `app/src/domain/user/services.py` -> `login_user` function.
        - After successful password check, update `user.last_login = datetime.now()`.
        - Commit the change (`db.commit()`).
    - **References**:
        - `app/src/domain/user/services.py:login_user`
    - **Acceptance Criteria**:
        - [ ] Login via `/api/user/v1/login`.
        - [ ] DB check shows updated timestamp.

- [ ] 4. **Implement Admin API: Unapprove & Detail**
    - **What to do**:
        - In `app/src/domain/admin/v1/router.py`:
        - Add `PATCH /users/{user_id}/unapprove`:
            - Call repository to set `is_active=False`.
            - Return updated user.
        - Add `GET /users/{user_id}`:
            - Fetch user with `selectinload(User.keywords)`.
            - Create and use `UserDetailResponse` (inherits `UserResponse`, adds `keywords: list[KeywordResponse]`).
    - **References**:
        - `app/src/domain/admin/v1/router.py`: Existing endpoints.
        - `app/src/domain/admin/schemas.py`: Add `UserDetailResponse` here.
        - `app/src/domain/user/repositories.py`: Add `get_user_with_keywords` method.
    - **Acceptance Criteria**:
        - [ ] `curl -X PATCH .../unapprove` deactivates user.
        - [ ] `curl .../users/{id}` returns user + keywords.

- [ ] 5. **Frontend: Admin List Update**
    - **What to do**:
        - Update `static/admin.html`: Add table header `<th>최근 접속</th>`.
        - Update `static/js/admin.js`:
            - In `renderUsers()`: Add column for `last_login` (format: YYYY-MM-DD HH:mm).
            - Add "승인 해제" button if user is active.
            - Bind click event to "승인 해제" button -> call API `unapprove`.
            - Make nickname clickable -> `window.location.href = 'admin_user_detail.html?id=' + user.id`.
    - **References**:
        - `static/admin.html`
        - `static/js/admin.js`
    - **Acceptance Criteria**:
        - [ ] Page shows last login times.
        - [ ] Unapprove button works.
        - [ ] Clicking nickname opens detail page.

- [ ] 6. **Frontend: Create User Detail Page**
    - **What to do**:
        - Create `static/admin_user_detail.html`:
            - Basic layout (navbar, container).
            - Sections: User Info (Table), Keywords (List/Table).
            - "Back to List" button.
        - Create `static/js/admin_user_detail.js`:
            - `window.onload`: Get `id` from URL params.
            - Call `GET /api/admin/v1/users/{id}`.
            - Render data into HTML elements.
    - **References**:
        - Copy structure from `static/admin.html` for consistency.
    - **Acceptance Criteria**:
        - [ ] Detail page loads correctly.
        - [ ] Shows User Email, Nickname, Status, Last Login.
        - [ ] Shows list of registered keywords.

- [ ] 7. **Git Push (No Merge)**
    - **What to do**:
        - Verify all changes are committed.
        - Push the feature branch to remote.
    - **Command**: `git push origin feature/admin-user-enhancement`
    - **Constraint**: DO NOT create a Pull Request or Merge.
    - **Acceptance Criteria**:
        - [ ] Remote branch exists.
        - [ ] Local branch matches remote.

---

## Success Criteria

1. **Functional**:
   - Admin can see when users last logged in.
   - Admin can block (unapprove) users.
   - Admin can inspect what keywords a user is tracking.
2. **Technical**:
   - Database schema migrated safely.
   - API response times remain under 200ms (efficient query loading).
