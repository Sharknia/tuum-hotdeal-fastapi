import hashlib

import bcrypt


def get_token_hash(token: str) -> str:
    """
    토큰을 SHA-256으로 해싱하여 반환합니다.
    DB 유출 시 원본 토큰 노출을 방지합니다.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """
    입력된 비밀번호와 해시된 비밀번호를 비교하여 검증합니다.
    """
    return bcrypt.checkpw(
        plain_password.encode("utf-8"), hashed_password.encode("utf-8")
    )


def hash_password(password: str) -> str:
    """
    비밀번호를 해싱하여 반환합니다.
    """
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")
