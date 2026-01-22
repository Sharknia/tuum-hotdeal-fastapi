import enum


class AuthLevel(int, enum.Enum):
    USER = 1
    ADMIN = 9
