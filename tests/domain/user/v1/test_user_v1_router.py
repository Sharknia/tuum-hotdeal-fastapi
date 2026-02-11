import pytest
from fastapi import Response

from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.domain.user.schemas import LogoutResponse


def _assert_auth_error_response(response: Response, auth_error) -> None:
    assert response.status_code == auth_error.status_code
    assert response.json() == {
        "description": auth_error.description,
        "detail": auth_error.detail,
    }


def _get_openapi_get_responses(mock_client, path: str) -> dict:
    response: Response = mock_client.get("/openapi.json")
    assert response.status_code == 200
    return response.json()["paths"][path]["get"]["responses"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_data, expected_status, mock_side_effect, expected_response",
    [
        # 정상 요청
        (
            {
                "email": "test@example.com",
                "password": "password123",
                "nickname": "test_user",
            },
            201,
            None,
            None,
        ),
        # 이메일 중복
        (
            {
                "email": "duplicate@example.com",
                "password": "password123",
                "nickname": "duplicate_user",
            },
            AuthErrors.EMAIL_ALREADY_REGISTERED.status_code,
            AuthErrors.EMAIL_ALREADY_REGISTERED,
            {
                "description": AuthErrors.EMAIL_ALREADY_REGISTERED.description,
                "detail": AuthErrors.EMAIL_ALREADY_REGISTERED.detail,
            },
        ),
    ],
)
async def test_post_user(
    mocker,
    add_mock_user,
    mock_client,
    mock_user_data,
    request_data,
    expected_status,
    mock_side_effect,
    expected_response,
):
    """회원가입 API 테스트"""
    # 중복 검사를 위한 기존 유저 추가
    await add_mock_user(
        email="duplicate@example.com",
        password="password123",
        nickname="duplicate_user",
        is_active=True,
    )
    if mock_side_effect:
        mocker.patch(
            "app.src.domain.user.services.create_new_user",
            side_effect=mock_side_effect,
        )
    else:
        mocker.patch(
            "app.src.domain.user.services.create_new_user",
            return_value=mock_user_data,
        )

    # API 호출
    response: Response = mock_client.post("/api/user/v1/", json=request_data)

    # 응답 검증
    assert response.status_code == expected_status

    if expected_response:
        assert response.json() == expected_response
    else:
        response_data = response.json()
        assert response_data["email"] == mock_user_data["email"]
        assert response_data["nickname"] == mock_user_data["nickname"]
        assert response_data["auth_level"] == mock_user_data["auth_level"]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_data, expected_status, mock_side_effect, expected_response",
    [
        # 정상 요청
        (
            {
                "email": "test@example.com",
                "password": "password123",
            },
            200,
            None,
            None,
        ),
        # 사용자 없음
        (
            {
                "email": "nonexistent@example.com",
                "password": "password123",
            },
            AuthErrors.USER_NOT_FOUND.status_code,
            AuthErrors.USER_NOT_FOUND,
            {
                "description": AuthErrors.USER_NOT_FOUND.description,
                "detail": AuthErrors.USER_NOT_FOUND.detail,
            },
        ),
        # 비밀번호 불일치
        (
            {
                "email": "test@example.com",
                "password": "wrong_password",
            },
            AuthErrors.INVALID_PASSWORD.status_code,
            AuthErrors.INVALID_PASSWORD,
            {
                "description": AuthErrors.INVALID_PASSWORD.description,
                "detail": AuthErrors.INVALID_PASSWORD.detail,
            },
        ),
        # 비활성 사용자
        (
            {
                "email": "inactive@example.com",
                "password": "password123",
            },
            AuthErrors.USER_NOT_ACTIVE.status_code,
            AuthErrors.USER_NOT_ACTIVE,
            {
                "description": AuthErrors.USER_NOT_ACTIVE.description,
                "detail": AuthErrors.USER_NOT_ACTIVE.detail,
            },
        ),
    ],
)
async def test_post_user_login(
    mocker,
    add_mock_user,
    mock_client,
    mock_user_data,
    request_data,
    expected_status,
    mock_side_effect,
    expected_response,
):
    """로그인 API 테스트"""
    # 정상 유저 추가
    await add_mock_user(
        email="test@example.com",
        password="password123",
        nickname="test_user",
        is_active=True,
    )
    # 비활성 유저 추가
    await add_mock_user(
        email="inactive@example.com",
        password="password123",
        nickname="inactive_user",
        is_active=False,
    )
    if mock_side_effect:
        mocker.patch(
            "app.src.domain.user.services.login_user",
            side_effect=mock_side_effect,
        )
    else:
        mocker.patch(
            "app.src.domain.user.services.login_user", return_value=mock_user_data
        )

    # API 호출
    response: Response = mock_client.post("/api/user/v1/login", json=request_data)

    # 응답 검증
    assert response.status_code == expected_status

    if expected_response:
        assert response.json() == expected_response
    else:
        response_data = response.json()
        # response_data안에 access_token, user_id가 있는지 확인
        assert "access_token" in response_data
        assert "user_id" in response_data


@pytest.mark.asyncio
async def test_post_user_logout(
    mocker,
    mock_authenticated_user,
    override_registered_user,
    mock_client,
):
    """로그아웃 API 테스트"""
    # 로그인 성공으로 오버라이드
    override_registered_user(mock_authenticated_user)

    mocker.patch(
        "app.src.domain.user.v1.router.logout_user",
        return_value=LogoutResponse(),
    )

    # API 호출
    headers = (
        {"Authorization": "Bearer some_refresh_token"}
        if mock_authenticated_user
        else {}
    )
    response: Response = mock_client.post("/api/user/v1/logout", headers=headers)

    # 응답 검증
    assert response.status_code == 200
    assert response.json() == {"message": "Logout successful"}


@pytest.mark.asyncio
async def test_get_me_inactive_user_returns_401(
    mocker,
    mock_client,
    mock_authenticated_user,
    override_registered_user,
    override_authenticate_user,
):
    override_registered_user(mock_authenticated_user)
    override_authenticate_user(error=AuthErrors.USER_NOT_ACTIVE)

    mocker.patch(
        "app.src.domain.user.v1.router.get_user_info",
        return_value={
            "id": "00000000-0000-0000-0000-00000000000a",
            "email": "test@example.com",
            "nickname": "test_user",
            "is_active": True,
            "auth_level": 1,
            "last_login": None,
            "created_at": "2024-12-31T12:00:00Z",
        },
    )

    response: Response = mock_client.get("/api/user/v1/me")

    _assert_auth_error_response(response, AuthErrors.USER_NOT_ACTIVE)


@pytest.mark.asyncio
async def test_logout_keeps_registered_user_dependency(
    mocker,
    mock_authenticated_user,
    override_registered_user,
    override_authenticate_user,
    mock_client,
):
    override_registered_user(mock_authenticated_user)
    override_authenticate_user(error=AuthErrors.USER_NOT_ACTIVE)

    mocker.patch(
        "app.src.domain.user.v1.router.logout_user",
        return_value=LogoutResponse(),
    )

    response: Response = mock_client.post(
        "/api/user/v1/logout",
        headers={"Authorization": "Bearer some_refresh_token"},
    )

    assert response.status_code == 200
    assert response.json() == {"message": "Logout successful"}


def test_get_me_openapi_includes_auth_error_response(mock_client):
    responses = _get_openapi_get_responses(mock_client, "/api/user/v1/me")

    assert "200" in responses
    assert "401" in responses
