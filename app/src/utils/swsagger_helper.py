from typing import Any

from app.src.core.exceptions.base_exceptions import BaseHTTPException


def create_responses(
    *error_responses: BaseHTTPException,
) -> dict[int, dict[str, Any]]:
    """
    에러 응답을 동적으로 생성하는 헬퍼 함수
    """
    return {
        error.status_code: {
            "description": error.description or "",
            "content": {"application/json": {"example": {"detail": error.detail}}},
        }
        for error in error_responses
    }
