from fastapi import status

from app.src.core.exceptions.base_exceptions import BaseHTTPException


class ClientErrors:
    # 키워드 갯수 초과
    KEYWORD_COUNT_OVERFLOW = BaseHTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Keyword count overflow",
        description="BAD REQUEST",
    )

    # 중복 키워드 등록
    DUPLICATE_KEYWORD_REGISTRATION = BaseHTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Duplicate keyword registration",
        description="DUPLICATE KEYWORD REGISTRATION",
    )

    # 키워드 존재하지 않음
    KEYWORD_NOT_FOUND = BaseHTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Keyword not found",
        description="KEYWORD NOT FOUND",
    )

    # 키워드 제목이 유효하지 않음
    INVALID_KEYWORD_TITLE = BaseHTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Invalid keyword title",
        description="INVALID KEYWORD TITLE",
    )
