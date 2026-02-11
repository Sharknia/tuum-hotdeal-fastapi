from datetime import datetime

import pytest
from fastapi import Response

from app.src.core.exceptions.auth_excptions import AuthErrors
from app.src.core.exceptions.client_exceptions import ClientErrors
from app.src.domain.hotdeal.schemas import KeywordResponse


def _assert_auth_error_response(response: Response, auth_error) -> None:
    assert response.status_code == auth_error.status_code
    assert response.json() == {
        "description": auth_error.description,
        "detail": auth_error.detail,
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "request_data, expected_status, mock_side_effect, expected_response",
    [
        # 정상 요청
        (
            {
                "id": 1,
                "title": "Keyword",
            },
            201,
            None,
            {
                "id": 1,
                "title": "keyword",
            },
        ),
        # 키워드 갯수 초과
        (
            {
                "id": 1,
                "title": "Keyword",
            },
            ClientErrors.KEYWORD_COUNT_OVERFLOW.status_code,
            ClientErrors.KEYWORD_COUNT_OVERFLOW,
            {
                "description": ClientErrors.KEYWORD_COUNT_OVERFLOW.description,
                "detail": ClientErrors.KEYWORD_COUNT_OVERFLOW.detail,
            },
        ),
    ],
)
async def test_post_keyword(
    mocker,
    mock_client,
    mock_authenticated_user,
    override_authenticate_user,
    request_data,
    expected_status,
    mock_side_effect,
    expected_response,
):
    """키워드 등록 API 테스트"""
    # 테스트용 인증 유저 오버라이드
    override_authenticate_user(mock_authenticated_user)

    if mock_side_effect:
        mocker.patch(
            "app.src.domain.hotdeal.v1.router.register_keyword",
            side_effect=mock_side_effect,
        )
    else:
        mocker.patch(
            "app.src.domain.hotdeal.v1.router.register_keyword",
            return_value=KeywordResponse(id=1, title="keyword", wdate=datetime.now()),
        )

    # API 호출
    response: Response = mock_client.post("/api/hotdeal/v1/keywords", json=request_data)

    # 응답 검증
    assert response.status_code == expected_status

    if expected_response:
        response_data = response.json()
        if isinstance(response_data, dict) and "wdate" in response_data:
            del response_data["wdate"]
        assert response_data == expected_response
    else:
        response_data = response.json()
        assert response_data["title"] == "keyword"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "keyword_id, expected_status, mock_side_effect, expected_response",
    [
        # 정상 요청
        (
            1,
            204,
            None,
            None,
        ),
        # 키워드 존재하지 않음
        (
            1,
            ClientErrors.KEYWORD_NOT_FOUND.status_code,
            ClientErrors.KEYWORD_NOT_FOUND,
            None,
        ),
    ],
)
async def test_delete_my_keyword(
    mocker,
    mock_client,
    mock_authenticated_user,
    override_authenticate_user,
    keyword_id,
    expected_status,
    mock_side_effect,
    expected_response,
):
    """내 키워드 삭제 API 테스트"""
    # 테스트용 인증 유저 오버라이드
    override_authenticate_user(mock_authenticated_user)

    if mock_side_effect:
        mocker.patch(
            "app.src.domain.hotdeal.v1.router.unlink_keyword",
            side_effect=mock_side_effect,
        )
    else:
        mocker.patch(
            "app.src.domain.hotdeal.v1.router.unlink_keyword",
            return_value=None,
        )

    # API 호출
    response: Response = mock_client.delete(f"/api/hotdeal/v1/keywords/{keyword_id}")

    # 응답 검증
    assert response.status_code == expected_status

    if expected_response:
        assert response.json() == expected_response


@pytest.mark.asyncio
async def test_get_my_keywords_list(
    mocker,
    mock_client,
    mock_authenticated_user,
    override_authenticate_user,
):
    """내 키워드 리스트 조회 API 테스트"""
    # 테스트용 인증 유저 오버라이드
    override_authenticate_user(mock_authenticated_user)

    mocker.patch(
        "app.src.domain.hotdeal.v1.router.view_users_keywords",
        return_value=[KeywordResponse(id=1, title="keyword", wdate=datetime.now())],
    )
    # API 호출
    response: Response = mock_client.get("/api/hotdeal/v1/keywords")

    # 응답 검증
    assert response.status_code == 200
    response_data = response.json()
    for item in response_data:
        if "wdate" in item:
            del item["wdate"]
    assert response_data == [
        {"id": 1, "title": "keyword"},
    ]


class TestGetSitesEndpoint:
    def test_get_sites_returns_200(self, mock_client):
        # when
        response: Response = mock_client.get("/api/hotdeal/v1/sites")

        # then
        assert response.status_code == 200

    def test_get_sites_returns_list(self, mock_client):
        # when
        response: Response = mock_client.get("/api/hotdeal/v1/sites")

        # then
        assert isinstance(response.json(), list)
        assert len(response.json()) > 0

    def test_get_sites_contains_required_fields(self, mock_client):
        # when
        response: Response = mock_client.get("/api/hotdeal/v1/sites")

        # then
        for site in response.json():
            assert "name" in site
            assert "display_name" in site
            assert "search_url_template" in site

    def test_get_sites_contains_all_active_sites(self, mock_client):
        # given
        from app.src.Infrastructure.crawling.crawlers import get_active_sites

        # when
        response: Response = mock_client.get("/api/hotdeal/v1/sites")
        site_names = [site["name"] for site in response.json()]

        # then
        for site in get_active_sites():
            assert site.value in site_names

    def test_get_sites_no_auth_required(self, mock_client):
        # when
        response: Response = mock_client.get("/api/hotdeal/v1/sites")

        # then
        assert response.status_code == 200


@pytest.mark.asyncio
async def test_post_keyword_inactive_user_returns_401(
    mocker,
    mock_client,
    mock_authenticated_user,
    override_registered_user,
    override_authenticate_user,
):
    override_registered_user(mock_authenticated_user)
    override_authenticate_user(error=AuthErrors.USER_NOT_ACTIVE)

    mocker.patch(
        "app.src.domain.hotdeal.v1.router.register_keyword",
        return_value=KeywordResponse(id=1, title="keyword", wdate=datetime.now()),
    )

    response: Response = mock_client.post(
        "/api/hotdeal/v1/keywords",
        json={"title": "keyword"},
    )

    _assert_auth_error_response(response, AuthErrors.USER_NOT_ACTIVE)


@pytest.mark.asyncio
async def test_delete_keyword_inactive_user_returns_401(
    mocker,
    mock_client,
    mock_authenticated_user,
    override_registered_user,
    override_authenticate_user,
):
    override_registered_user(mock_authenticated_user)
    override_authenticate_user(error=AuthErrors.USER_NOT_ACTIVE)

    mocker.patch(
        "app.src.domain.hotdeal.v1.router.unlink_keyword",
        return_value=None,
    )

    response: Response = mock_client.delete("/api/hotdeal/v1/keywords/1")

    _assert_auth_error_response(response, AuthErrors.USER_NOT_ACTIVE)


@pytest.mark.asyncio
async def test_get_keywords_inactive_user_returns_401(
    mocker,
    mock_client,
    mock_authenticated_user,
    override_registered_user,
    override_authenticate_user,
):
    override_registered_user(mock_authenticated_user)
    override_authenticate_user(error=AuthErrors.USER_NOT_ACTIVE)

    mocker.patch(
        "app.src.domain.hotdeal.v1.router.view_users_keywords",
        return_value=[KeywordResponse(id=1, title="keyword", wdate=datetime.now())],
    )

    response: Response = mock_client.get("/api/hotdeal/v1/keywords")

    _assert_auth_error_response(response, AuthErrors.USER_NOT_ACTIVE)
