# Admin Dashboard Implementation Plan

## Context

### Original Request
Create an Admin Page with:
- Keyword Management (CRUD)
- Site-specific Keyword Management
- Worker Log Viewing
- User Management (Approval)
- Admin-only Header Access

### Technical Constraints
- **Backend**: FastAPI, SQLAlchemy (Async), Pydantic
- **Frontend**: Vanilla HTML/CSS/JS (Static Files)
- **Auth**: JWT-based, `AuthLevel` enum exists (USER, ADMIN)
- **Testing**: TDD required for backend logic

---

## Work Objectives

### Core Objective
Implement a secure, functional admin dashboard for managing the Hotdeal service.

### Concrete Deliverables
- **Backend**: `WorkerLog` model, Admin API endpoints (Users, Keywords, Logs).
- **Frontend**: `admin.html`, `js/admin.js`, updated header.
- **Worker**: Integrated logging to DB.

### Definition of Done
- [ ] Admin API endpoints pass all tests (`pytest`).
- [ ] Admin page is accessible only to users with `auth_level >= ADMIN`.
- [ ] Worker execution logs are visible in the dashboard.
- [ ] Users can be approved via dashboard.

---

## Verification Strategy

### Test Decision
- **Infrastructure exists**: YES (pytest)
- **User wants tests**: YES (TDD for backend)
- **Framework**: pytest

### TDD Workflow
1.  **RED**: Write failing test for Admin API endpoint.
2.  **GREEN**: Implement endpoint logic.
3.  **REFACTOR**: Optimize.

### Manual QA (Frontend)
- Login as Admin -> Verify "Admin" link appears.
- Login as User -> Verify "Admin" link is absent.
- Access `/admin` -> Verify data loads.
- Approve a user -> Verify status change.

---

## Task Flow

```
1. Feature Branch & DB Model (WorkerLog)
   ↓
2. Worker Integration (Log Logic)
   ↓
3. Backend TDD & Implementation (Admin API)
   ↓
4. Frontend Implementation (admin.html, admin.js)
   ↓
5. Integration (Header & Access Control)
```

---

## TODOs

- [x] 1. **Setup & Database Modeling**
    - **What to do**:
        - Create feature branch `feature/admin-page`.
        - Create `WorkerLog` model in `app/src/domain/admin/models.py` (or `hotdeal` if preferred, but Admin domain seems better for logs).
        - Fields: `id`, `run_at`, `status`, `items_found`, `message`, `details` (JSON/Text).
        - Generate Alembic migration and apply.
    - **References**:
        - `app/src/domain/mail/models.py` (Model pattern)
        - `alembic/` (Migration)
    - **Acceptance Criteria**:
        - `WorkerLog` table exists in DB.

- [x] 2. **Worker Logging Integration**
    - **What to do**:
        - Modify `app/worker_main.py` to write to `WorkerLog`.
        - Log start of job, end of job (success), and errors.
    - **References**:
        - `app/worker_main.py`
    - **Acceptance Criteria**:
        - Running `poetry run python -m app.worker_main` creates a log entry in DB.

- [x] 3. **Backend: User Management API (TDD)**
    - **What to do**:
        - **RED**: Create `tests/domain/admin/test_user_mgmt.py`. Test `GET /api/admin/users` and `PATCH /api/admin/users/{id}/approve`.
        - **GREEN**: Implement endpoints in `app/src/domain/admin/v1/router.py`.
    - **Acceptance Criteria**:
        - `GET` returns list of users with auth info.
        - `PATCH` updates `is_active` to True.

- [x] 4. **Backend: Keyword & Log API (TDD)**
    - **What to do**:
        - **RED**: Create `tests/domain/admin/test_resources.py`. Test `GET /api/admin/keywords`, `DELETE /api/admin/keywords/{id}`, `GET /api/admin/logs`.
        - **GREEN**: Implement endpoints.
    - **References**:
        - `app/src/domain/hotdeal/models.py` (Keyword)
    - **Acceptance Criteria**:
        - Endpoints return correct data structures.
        - Delete removes keyword and associated `KeywordSite` data (cascade check).

- [x] 5. **Frontend: Admin Page Structure**
    - **What to do**:
        - Create `static/admin.html` (copy layout from `hotdeal.html`).
        - Add sections: User Management, Keyword Management, Worker Logs.
    - **References**:
        - `static/hotdeal.html`
    - **Acceptance Criteria**:
        - Page loads at `/admin` (need to add route in `main.py` or just static file access).

- [x] 6. **Frontend: Admin Logic (`admin.js`)**
    - **What to do**:
        - Create `static/js/admin.js`.
        - Fetch users/keywords/logs from API.
        - Render tables.
        - Handle "Approve" and "Delete" button clicks.
    - **References**:
        - `static/js/keyword_manager.js` (Fetch patterns)
    - **Acceptance Criteria**:
        - Data populates dynamically.
        - Actions reflect in UI and persist to DB.

- [x] 7. **Frontend: Header & Access Control**
    - **What to do**:
        - Update shared header logic (likely in `static/hotdeal.html` and `static/admin.html` scripts, or extract to `nav.js` if possible, but minimal change preferred).
        - Check `userInfo.auth_level`. If `ADMIN` (value 99 or similar, check Enum), show "Admin" link.
        - In `admin.js`, redirect to `/login` if not admin.
    - **References**:
        - `app/src/domain/user/enums.py` (AuthLevel values)
        - `static/js/auth.js`
    - **Acceptance Criteria**:
        - Admin link visible ONLY for admins.
        - Non-admins redirected from `/admin`.

---

## Commit Strategy
- `feat(admin): add WorkerLog model and migration`
- `feat(worker): integrate DB logging`
- `feat(api): add admin user management endpoints`
- `feat(api): add admin resource endpoints`
- `feat(ui): add admin dashboard page`
- `feat(ui): update navigation for admin access`
