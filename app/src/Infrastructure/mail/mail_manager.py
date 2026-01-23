from email.mime.text import MIMEText
from html import escape
from itertools import groupby

import aiosmtplib

from app.src.core.config import settings
from app.src.core.logger import logger
from app.src.domain.hotdeal.models import Keyword
from app.src.domain.hotdeal.schemas import CrawledKeyword


async def make_hotdeal_email_content(
    keyword: Keyword,
    updates: list[CrawledKeyword],
) -> str:
    """
    핫딜 업데이트 내용을 메일 형식으로 변환.
    사이트별로 그룹화하여 표시합니다.
    """
    if not updates:
        return ""

    # 사이트별로 정렬 후 그룹화
    sorted_updates = sorted(updates, key=lambda x: x.site_name.value)

    html = f"<h2>{escape(keyword.title)} 새 핫딜</h2>"

    for site_name, products in groupby(sorted_updates, key=lambda x: x.site_name):
        products_list = list(products)
        search_url = products_list[0].search_url
        site_display = site_name.value.upper()

        html += f"<h3><a href='{escape(search_url)}'>[{site_display}] 검색 결과</a></h3>"
        html += "".join(
            [
                f"<p><a href='{escape(product.link)}'>{escape(product.title)}</a> - {escape(product.price or '')}</p>"
                for product in products_list
            ]
        )

    return html


async def send_email(
    subject: str,
    to: str,
    body: str = "",
    sender: str = settings.SMTP_FROM,
    is_html: bool = False,
):
    try:
        msg = MIMEText(body, "html" if is_html else "plain")  # HTML 형식 지원
        msg["Subject"] = subject
        msg["From"] = sender
        msg["To"] = to

        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_SERVER,
            port=settings.SMTP_PORT,
            use_tls=True,
            username=settings.SMTP_EMAIL,
            password=settings.SMTP_PASSWORD,
            sender=sender,
            recipients=to,
        )

        # TODO: 메일 전송 로그 남기기
        logger.info(f"메일 전송 완료! 수신자: {to}")
    except Exception as e:
        logger.error(f"메일 전송 실패: {e}")
