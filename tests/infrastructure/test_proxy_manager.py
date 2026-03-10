from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.src.core.config import settings
from app.src.Infrastructure.crawling.proxy_manager import (
    ProxyFailureType,
    ProxyManager,
)

HTML_WITH_SINGLE_PROXY = b"""
<table class="table table-striped table-bordered">
  <tbody>
    <tr>
      <td>10.0.0.1</td><td>8080</td><td></td><td></td><td>anonymous</td><td></td><td>yes</td>
    </tr>
  </tbody>
</table>
"""


def build_proxy_table(rows: list[tuple[str, int, str, str]]) -> bytes:
    html_rows = []
    for host, port, anonymity, https in rows:
        html_rows.append(
            "<tr>"
            f"<td>{host}</td><td>{port}</td><td></td><td></td>"
            f"<td>{anonymity}</td><td></td><td>{https}</td>"
            "</tr>"
        )
    return (
        "<table class='table table-striped table-bordered'><tbody>"
        + "".join(html_rows)
        + "</tbody></table>"
    ).encode()


class FakeResponse:
    content = HTML_WITH_SINGLE_PROXY

    def raise_for_status(self):
        return None


@pytest.fixture
def proxy_manager():
    manager = ProxyManager()
    manager.reset_proxies(clear_history=True)
    yield manager
    manager.reset_proxies(clear_history=True)


def test_classify_failure_type():
    assert ProxyManager.classify_failure(status_code=403) == ProxyFailureType.BLOCKED
    assert ProxyManager.classify_failure(status_code=503) == ProxyFailureType.SERVER
    assert ProxyManager.classify_failure(
        error=RuntimeError("connection attempts failed")
    ) == ProxyFailureType.NETWORK
    assert ProxyManager.classify_failure(
        error=RuntimeError("SSL verify failed")
    ) == ProxyFailureType.SSL
    assert ProxyManager.classify_failure(error=RuntimeError("unknown")) == ProxyFailureType.UNKNOWN


def test_soft_hard_ban_state_transition(proxy_manager):
    proxy_url = "http://1.1.1.1:8080"
    proxy_manager.register_proxy(proxy_url)

    with (
        patch.object(settings, "PROXY_SOFT_BAN_FAILURE_THRESHOLD", 2),
        patch.object(settings, "PROXY_HARD_BAN_FAILURE_THRESHOLD", 3),
        patch.object(settings, "PROXY_SOFT_BAN_TTL_SECONDS", 60),
    ):
        first = proxy_manager.record_proxy_failure(proxy_url, ProxyFailureType.NETWORK)
        assert first.failure_count == 1
        assert first.soft_ban_until is None
        assert first.is_hard_banned is False

        second = proxy_manager.record_proxy_failure(proxy_url, ProxyFailureType.NETWORK)
        assert second.failure_count == 2
        assert second.soft_ban_until is not None
        assert second.is_hard_banned is False

        third = proxy_manager.record_proxy_failure(proxy_url, ProxyFailureType.BLOCKED)
        assert third.failure_count == 3
        assert third.is_hard_banned is True
        assert third.soft_ban_until is None


def test_soft_ban_ttl_expire_restores_active(proxy_manager):
    proxy_url = "http://2.2.2.2:8080"
    proxy_manager.register_proxy(proxy_url)

    with (
        patch.object(settings, "PROXY_SOFT_BAN_FAILURE_THRESHOLD", 1),
        patch.object(settings, "PROXY_HARD_BAN_FAILURE_THRESHOLD", 10),
        patch.object(settings, "PROXY_SOFT_BAN_TTL_SECONDS", 60),
    ):
        state = proxy_manager.record_proxy_failure(proxy_url, ProxyFailureType.BLOCKED)
        assert state.soft_ban_until is not None

        state.soft_ban_until = datetime.now(UTC) - timedelta(seconds=1)
        next_proxy = proxy_manager.get_next_proxy()

        assert next_proxy == proxy_url
        assert state.soft_ban_until is None


def test_failed_proxy_not_reintroduced_across_batches(proxy_manager):
    proxy_url = "http://10.0.0.1:8080"

    with (
        patch.object(settings, "PROXY_SOFT_BAN_FAILURE_THRESHOLD", 1),
        patch.object(settings, "PROXY_HARD_BAN_FAILURE_THRESHOLD", 1),
        patch.object(settings, "PROXY_HEALTHCHECK_ENABLED", False),
        patch("app.src.Infrastructure.crawling.proxy_manager.requests.get", return_value=FakeResponse()),
    ):
        proxy_manager.fetch_proxies()
        proxy_manager.record_proxy_failure(proxy_url, ProxyFailureType.BLOCKED)
        assert proxy_manager.get_proxy_state(proxy_url).is_hard_banned is True

        proxy_manager.reset_proxies(clear_history=False)
        proxy_manager.fetch_proxies()

    assert proxy_url not in list(proxy_manager.proxies)
    assert proxy_manager.get_next_proxy() is None


def test_extract_proxies_from_html_collects_full_table_without_limit(proxy_manager):
    html = build_proxy_table(
        [
            (f"8.8.8.{index}", 8000 + index, "anonymous" if index % 2 else "transparent", "yes")
            for index in range(1, 41)
        ]
    )

    proxies = proxy_manager._extract_proxies_from_html(html)

    assert len(proxies) == 40
    assert proxies[0] == "http://8.8.8.1:8001"
    assert proxies[-1] == "http://8.8.8.40:8040"


def test_fetch_proxies_logs_candidate_pool_breakdown(proxy_manager):
    html = build_proxy_table(
        [
            ("10.0.0.1", 8080, "anonymous", "yes"),
            ("10.0.0.2", 8081, "transparent", "no"),
        ]
    )

    class FakeTableResponse:
        content = html

        def raise_for_status(self):
            return None

    proxy_manager.register_proxy("http://10.0.0.1:8080")

    with (
        patch.object(settings, "PROXY_HEALTHCHECK_ENABLED", False),
        patch(
            "app.src.Infrastructure.crawling.proxy_manager.requests.get",
            return_value=FakeTableResponse(),
        ),
        patch("app.src.Infrastructure.crawling.proxy_manager.logger.info") as mock_logger_info,
    ):
        proxy_manager.fetch_proxies()

    summary_calls = [
        call
        for call in mock_logger_info.call_args_list
        if call.args and call.args[0].startswith("프록시 수집 결과:")
    ]
    assert summary_calls
    summary_message = summary_calls[-1].args[0]
    assert "skipped_existing=%s" in summary_message
    assert "pool_size_before=%s" in summary_message
    assert "pool_size_after=%s" in summary_message
    assert "active=%s" in summary_message


def test_replenish_loop_triggers_until_min_available(proxy_manager):
    proxy_manager.register_proxy("http://1.1.1.1:8080")

    fetch_call_count = {"count": 0}

    def fake_fetch():
        fetch_call_count["count"] += 1
        if fetch_call_count["count"] == 1:
            proxy_manager.register_proxy("http://1.1.1.2:8080")
        if fetch_call_count["count"] == 2:
            proxy_manager.register_proxy("http://1.1.1.3:8080")
        return list(proxy_manager.proxies)

    with (
        patch.object(settings, "PROXY_REPLENISH_ATTEMPTS", 3),
        patch.object(proxy_manager, "fetch_proxies", side_effect=fake_fetch),
    ):
        assert proxy_manager.ensure_min_available_proxies(3) is True

    assert fetch_call_count["count"] == 2
    assert proxy_manager.get_available_proxy_count() == 3


def test_healthcheck_rejects_non_public_proxy_endpoint(proxy_manager):
    with (
        patch.object(settings, "PROXY_HEALTHCHECK_ENABLED", True),
        patch("app.src.Infrastructure.crawling.proxy_manager.requests.get") as mock_get,
    ):
        assert proxy_manager._is_proxy_healthy("http://127.0.0.1:8080") is False
    mock_get.assert_not_called()


def test_healthcheck_accepts_public_proxy_endpoint(proxy_manager):
    fake_response = FakeResponse()
    fake_response.status_code = 200
    with (
        patch.object(settings, "PROXY_HEALTHCHECK_ENABLED", True),
        patch("app.src.Infrastructure.crawling.proxy_manager.requests.get", return_value=fake_response) as mock_get,
    ):
        assert proxy_manager._is_proxy_healthy("http://1.1.1.1:8080") is True
    mock_get.assert_called_once()


def test_get_metrics_does_not_mutate_soft_ban_state(proxy_manager):
    proxy_url = "http://1.1.1.1:8080"
    proxy_manager.register_proxy(proxy_url)
    state = proxy_manager.get_proxy_state(proxy_url)
    assert state is not None
    state.soft_ban_until = datetime.now(UTC) - timedelta(seconds=1)

    metrics = proxy_manager.get_metrics()

    assert metrics["active_proxy_count"] == 1
    assert state.soft_ban_until is not None

    next_proxy = proxy_manager.get_next_proxy()
    assert next_proxy == proxy_url
    assert state.soft_ban_until is None


def test_rehabilitate_proxy_history_restores_only_targeted_failures(proxy_manager):
    blocked_proxy = "http://1.1.1.1:8080"
    unknown_proxy = "http://1.1.1.2:8080"
    network_proxy = "http://1.1.1.3:8080"
    for proxy_url in (blocked_proxy, unknown_proxy, network_proxy):
        proxy_manager.register_proxy(proxy_url)

    with (
        patch.object(settings, "PROXY_SOFT_BAN_FAILURE_THRESHOLD", 1),
        patch.object(settings, "PROXY_HARD_BAN_FAILURE_THRESHOLD", 2),
        patch.object(settings, "PROXY_SOFT_BAN_TTL_SECONDS", 60),
    ):
        blocked_state = proxy_manager.record_proxy_failure(
            blocked_proxy, ProxyFailureType.BLOCKED
        )
        unknown_state = proxy_manager.record_proxy_failure(
            unknown_proxy, ProxyFailureType.UNKNOWN
        )
        proxy_manager.record_proxy_failure(network_proxy, ProxyFailureType.NETWORK)
        proxy_manager.record_proxy_failure(network_proxy, ProxyFailureType.NETWORK)

    summary = proxy_manager.rehabilitate_proxy_history(
        failure_types={ProxyFailureType.BLOCKED, ProxyFailureType.UNKNOWN},
        reason="algumon_search_endpoint_migration",
    )

    assert summary == {
        "reset": 2,
        "released_soft_bans": 2,
        "released_hard_bans": 0,
        "requeued": 0,
    }
    assert blocked_state.failure_count == 0
    assert blocked_state.soft_ban_until is None
    assert blocked_state.is_hard_banned is False
    assert unknown_state.failure_count == 0
    assert unknown_state.soft_ban_until is None
    assert unknown_state.is_hard_banned is False

    preserved_state = proxy_manager.get_proxy_state(network_proxy)
    assert preserved_state is not None
    assert preserved_state.failure_count == 2
    assert preserved_state.is_hard_banned is True
