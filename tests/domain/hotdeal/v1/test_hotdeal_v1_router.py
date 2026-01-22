import pytest
from fastapi import Response

from app.src.core.exceptions.client_exceptions import ClientErrors
from app.src.domain.hotdeal.schemas import KeywordResponse


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
    override_registered_user,
    request_data,
    expected_status,
    mock_side_effect,
    expected_response,
):
    """키워드 등록 API 테스트"""
    # 테스트용 인증 유저 오버라이드
    override_registered_user(mock_authenticated_user)

    if mock_side_effect:
        mocker.patch(
            "app.src.domain.hotdeal.v1.router.register_keyword",
            side_effect=mock_side_effect,
        )
    else:
        mocker.patch(
            "app.src.domain.hotdeal.v1.router.register_keyword",
            return_value=KeywordResponse(id=1, title="keyword"),
        )

    # API 호출
    response: Response = mock_client.post("/api/hotdeal/v1/keywords", json=request_data)

    # 응답 검증
    assert response.status_code == expected_status

    if expected_response:
        assert response.json() == expected_response
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
    override_registered_user,
    keyword_id,
    expected_status,
    mock_side_effect,
    expected_response,
):
    """내 키워드 삭제 API 테스트"""
    # 테스트용 인증 유저 오버라이드
    override_registered_user(mock_authenticated_user)

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
    override_registered_user,
):
    """내 키워드 리스트 조회 API 테스트"""
    # 테스트용 인증 유저 오버라이드
    override_registered_user(mock_authenticated_user)

    mocker.patch(
        "app.src.domain.hotdeal.v1.router.view_users_keywords",
        return_value=[KeywordResponse(id=1, title="keyword")],
    )
    # API 호출
    response: Response = mock_client.get("/api/hotdeal/v1/keywords")

    # 응답 검증
    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "title": "keyword"},
    ]
