from pathlib import Path


def test_login_page_contains_split_feedback_ui(mock_client):
    response = mock_client.get("/login")

    assert response.status_code == 200
    assert 'id="login-feedback"' in response.text
    assert "관리자 승인 완료 전까지 로그인할 수 없습니다." in response.text


def test_signup_page_contains_pending_approval_notice(mock_client):
    response = mock_client.get("/signup")

    assert response.status_code == 200
    assert 'id="signup-pending"' in response.text
    assert "승인 대기" in response.text
    assert "로그인 페이지로 이동" in response.text


def test_login_script_maps_backend_login_error_details():
    script = Path("static/login.js").read_text(encoding="utf-8")

    assert "User account is not active" in script
    assert "Invalid password" in script
    assert "User not found" in script
    assert "가입 승인 대기 중입니다." in script


def test_signup_script_shows_pending_approval_state():
    script = Path("static/signup.js").read_text(encoding="utf-8")

    assert "showPendingApprovalState" in script
    assert "가입된 이메일입니다" in script or "이미 가입된 이메일입니다" in script
    assert "승인 대기" in Path("static/signup.html").read_text(encoding="utf-8")
