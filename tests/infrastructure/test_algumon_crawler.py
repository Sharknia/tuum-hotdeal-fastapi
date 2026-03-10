from unittest.mock import MagicMock

from app.src.domain.hotdeal.enums import SiteName
from app.src.Infrastructure.crawling.crawlers.algumon import AlgumonCrawler

ALGUMON_SEARCH_HTML = """
<div class="flex flex-col gap-1.5 bg-base-200 py-1.5 svelte-17cy2qz">
  <div class="card bg-base-100 rounded-none border-y border-base-content/10 sm:border-x" id="deal-935508">
    <div class="card-body gap-1 pt-3 px-3 pb-0">
      <div class="deal-card-content tracking-tight svelte-11qv2qb">
        <div>
          <div class="flex items-center gap-1 mb-1.5">
            <span class="badge badge-soft badge-xs rounded-sm gap-1">퀘이사존</span>
          </div>
          <h3 class="font-medium text-base leading-[1.15] line-clamp-2 break-all mb-0.5 svelte-11qv2qb">
            <a class="hover:text-primary transition-colors" href="https://www.algumon.com/l/d/935508?v=abc&t=123" rel="noopener noreferrer" target="_blank">
              안텍 <mark class="bg-warning/40 text-inherit">테스트</mark> 상품
            </a>
          </h3>
          <p class="text-sm font-semibold deal-price-text">1원</p>
          <div class="flex items-center gap-1 text-xs text-base-content/70 mb-1 mt-1">
            <span>배송 무료</span>
            <span>·</span>
            <span class="text-base-content/60">26. 02. 06.</span>
          </div>
          <div class="flex gap-2 text-xs text-base-content/60 -mt-0.5 mb-0.5">
            <span class="flex items-center gap-1"><span class="font-medium">5</span></span>
            <span class="flex items-center gap-1">길가던노랭이</span>
          </div>
          <a class="flex items-center justify-center w-6 shrink-0 text-base-content/30 hover:text-base-content/60 transition-colors" href="/n/deal/935508"></a>
        </div>
      </div>
    </div>
  </div>
</div>
"""


def test_algumon_crawler_builds_new_search_url():
    crawler = AlgumonCrawler(keyword="테스트 상품", client=MagicMock())

    assert (
        crawler.url
        == "https://www.algumon.com/n/deal?keyword=%ED%85%8C%EC%8A%A4%ED%8A%B8+%EC%83%81%ED%92%88"
    )
    assert crawler.search_url == crawler.url


def test_algumon_crawler_parses_new_deal_card_structure():
    crawler = AlgumonCrawler(keyword="테스트 상품", client=MagicMock())

    result = crawler.parse(ALGUMON_SEARCH_HTML)

    assert len(result) == 1
    first = result[0]
    assert first.id == "935508"
    assert first.title == "안텍 테스트 상품"
    assert first.link == "https://www.algumon.com/n/deal/935508"
    assert first.price == "1원"
    assert first.site_name == SiteName.ALGUMON
    assert first.search_url == crawler.search_url
    assert first.meta_data == "퀘이사존 | 배송 무료 · 26. 02. 06. | 5 길가던노랭이"
