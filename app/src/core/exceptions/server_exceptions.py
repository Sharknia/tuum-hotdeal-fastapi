from fastapi import status

from app.src.core.exceptions.base_exceptions import BaseHTTPException


class ServerErrors:
    # 외부 API 응답 형식 오류
    EXTERNAL_API_INVALID_RESPONSE = BaseHTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Invalid response format from external API",
        description="Invalid External API Response",
    )

    # 외부 API 호출 실패
    EXTERNAL_API_FETCH_FAILED = BaseHTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Failed to fetch assets from external API",
        description="Unavailable External API",
    )

    # 데이터베이스 작업 실패
    DATABASE_OPERATION_FAILED = BaseHTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database operation failed",
        description="INTERNAL SERVER ERROR",
    )

    # 이메일 전송 실패
    EMAIL_SEND_FAILED = BaseHTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Failed to send email",
        description="INTERNAL SERVER ERROR",
    )

    # 알 수 없는 서버 오류
    UNKNOWN_SERVER_ERROR = BaseHTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Unknown server error",
        description="INTERNAL SERVER ERROR",
    )
