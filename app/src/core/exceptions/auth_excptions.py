from fastapi import status

from app.src.core.exceptions.base_exceptions import BaseHTTPException


class AuthErrors:
    # 인증 오류
    NOT_AUTHENTICATED = BaseHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        description="Unauthorized",
        detail="Not authenticated",
    )

    # 잘못된 토큰으로 인한 인증 오류
    INVALID_TOKEN = BaseHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        description="Unauthorized",
        detail="Invalid token",
    )

    # 토큰 페이로드 오류
    INVALID_TOKEN_PAYLOAD = BaseHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        description="Unauthorized",
        detail="Invalid token payload",
    )

    # 토큰 만료 오류
    TOKEN_EXPIRED = BaseHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        description="Unauthorized",
        detail="Token expired",
    )

    # 액세스 토큰 만료 오류
    ACCESS_TOKEN_EXPIRED = BaseHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        description="Unauthorized",
        detail="Access token expired",
    )

    # 리프레시 토큰 만료 오류
    REFRESH_TOKEN_EXPIRED = BaseHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        description="Unauthorized",
        detail="Refresh token expired",
    )

    # 이메일 미인증 오류
    EMAIL_NOT_VERIFIED = BaseHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        description="Unauthorized",
        detail="Email is not verified",
    )

    # 비활성 사용자 오류
    USER_NOT_ACTIVE = BaseHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        description="Unauthorized",
        detail="User account is not active",
    )

    # 비밀번호 불일치 오류
    INVALID_PASSWORD = BaseHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        description="Unauthorized",
        detail="Invalid password",
    )

    # 이미 인증된 이메일 오류
    EMAIL_ALREADY_VERIFIED = BaseHTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        description="Bad Request",
        detail="Email already verified",
    )

    # 이미 등록된 이메일 오류
    EMAIL_ALREADY_REGISTERED = BaseHTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        description="Bad Request",
        detail="Email already registered",
    )

    # 등록되지 않은 이메일 오류
    NOT_REGISTERED = BaseHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        description="Not Registered",
        detail="Email not registered",
    )

    # 사용자 없음 오류
    USER_NOT_FOUND = BaseHTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        description="Not Found",
        detail="User not found",
    )

    # 권한 부족 오류
    INSUFFICIENT_PERMISSIONS = BaseHTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        description="Forbidden",
        detail="Insufficient permissions",
    )
