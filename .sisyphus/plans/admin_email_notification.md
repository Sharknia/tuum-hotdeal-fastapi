# Plan: Admin Email Notification for New User Signup (DB Based)

## Context
The user wants to notify **all admin users** via email when a new user signs up. The list of admins must be retrieved dynamically from the database (`users` table where `auth_level=ADMIN`), avoiding environment variables for this purpose.

## Work Objectives
- **Core Objective**: Notify all administrators dynamically upon new user signup.
- **Deliverables**:
    - Repository method to fetch all admin emails.
    - Service function to handle the broadcasting.
    - Router update to trigger this flow asynchronously.
- **Definition of Done**:
    - `get_all_admins` returns all users with `AuthLevel.ADMIN`.
    - Signing up triggers emails to all found admins.
    - Tests and Linting pass.
    - Changes pushed to `feature/admin-email-noti`.

## Verification Strategy
- **Manual QA**:
    - **Pre-requisite**: Ensure at least one user in DB has `auth_level=9` (ADMIN).
    - **Action**: Create a new user via `/api/user/v1/signup`.
    - **Verification**: Check logs for multiple "메일 전송 완료" messages (one per admin).

## Git & Quality Strategy
- **Branch**: `feature/admin-email-noti`
- **Pre-Commit Checks**:
    - Linting: `make lint` (or `ruff check .` + `mypy .`)
    - Testing: `pytest tests/domain/user`
- **Commit & Push**:
    - Commit Message: `feat: implement admin email notification on signup`
    - Push: `git push -u origin feature/admin-email-noti`
    - **Constraint**: DO NOT MERGE (PR only).

## Task Flow
1.  Setup Branch.
2.  Implement `get_all_admins` in repository.
3.  Implement `send_admin_notifications` in service.
4.  Update `signup` router to wire it up.
5.  Verify (Manual + Automated).
6.  Commit and Push.

## TODOs

- [ ] 0. Setup Git Branch
    - **What to do**:
        - Create and switch to branch `feature/admin-email-noti`.

- [x] 1. Add `get_all_admins` to `app/src/domain/user/repositories.py`
    - **What to do**:
        - Implement function `async def get_all_admins(db: AsyncSession) -> list[str]`.
        - Query: `select(User.email).where(User.auth_level == AuthLevel.ADMIN)`.
        - Return list of email strings.
    - **References**:
        - `app/src/domain/user/repositories.py`
        - `app/src/domain/user/enums.py` (for `AuthLevel.ADMIN`)
    - **Acceptance Criteria**:
        - Returns list of emails for all admins.

- [x] 2. Add notification logic to `app/src/domain/user/services.py`
    - **What to do**:
        - Import `send_email` from `app.src.Infrastructure.mail.mail_manager`.
        - Create async function `send_new_user_notifications(admin_emails: list[str], user: UserResponse)`.
        - Loop through `admin_emails` and call `send_email` for each.
        - **Subject**: `[Tuum] 신규 회원 가입: {user.nickname}`
        - **Body**:
            ```text
            새로운 회원이 가입했습니다.
            이메일: {user.email}
            닉네임: {user.nickname}
            관리자: https://hotdeal.tuum.day/admin
            ```
    - **References**:
        - `app/src/domain/user/services.py`
        - `app/src/Infrastructure/mail/mail_manager.py`
    - **Acceptance Criteria**:
        - Sends email to all recipients in the list.
        - Handles exceptions safely (log error but don't fail).

- [x] 3. Update `signup` router in `app/src/domain/user/v1/router.py`
    - **What to do**:
        - Inject `background_tasks: BackgroundTasks`.
        - Import `get_all_admins` from repositories.
        - Import `send_new_user_notifications` from services.
        - Inside `signup`:
            - `admins = await get_all_admins(db)`
            - `if admins: background_tasks.add_task(send_new_user_notifications, admins, new_user)`
    - **References**:
        - `app/src/domain/user/v1/router.py`
    - **Acceptance Criteria**:
        - Background task is scheduled with admin list.
        - Signup response is immediate.

- [x] 4. Quality Checks & Verification
    - **What to do**:
        - Update a test user to ADMIN (if none exists) via DB or psql.
        - Sign up a new user manually.
        - Run `make lint` (or `ruff check .`).
        - Run `pytest tests/domain/user`.
    - **Acceptance Criteria**:
        - Logs confirm email sending to admin(s).
        - Lint checks pass.
        - Tests pass.

- [x] 5. Git Commit & Push
    - **What to do**:
        - `git add .`
        - `git commit -m "feat: send admin notification on user signup"`
        - `git push -u origin feature/admin-email-noti`
    - **Constraint**:
        - **DO NOT MERGE** to main.
