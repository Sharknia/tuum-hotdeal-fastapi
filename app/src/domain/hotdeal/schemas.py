from pydantic import BaseModel

from app.src.domain.hotdeal.enums import SiteName


class CrawledKeyword(BaseModel):
    id: str
    title: str
    link: str
    price: str | None = None
    meta_data: str | None = None
    site_name: SiteName
    search_url: str


class KeywordCreateRequest(BaseModel):
    title: str


class KeywordResponse(BaseModel):
    id: int
    title: str


class SiteInfo(BaseModel):
    name: SiteName
    display_name: str
    search_url_template: str
