from fastapi import HTTPException


class BaseHTTPException(HTTPException):
    """
    Base HTTP Exception with an optional description for responses.
    """

    def __init__(
        self,
        status_code: int,
        detail: str,
        description: str = None,
    ):
        super().__init__(
            status_code=status_code,
            detail=detail,
        )
        self.description = description
