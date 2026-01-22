from pydantic import BaseModel


class CrawledKeyword(BaseModel):
    id: str | None = None
    title: str | None = None
    link: str | None = None
    price: str | None = None
    meta_data: str | None = None


class KeywordCreateRequest(BaseModel):
    title: str


class KeywordResponse(BaseModel):
    id: int
    title: str
