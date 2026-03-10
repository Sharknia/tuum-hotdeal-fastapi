from collections import Counter, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from ipaddress import ip_address
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from app.src.core.config import settings
from app.src.core.logger import logger


class ProxyFailureType(str, Enum):
    BLOCKED = "blocked"
    NETWORK = "network"
    SSL = "ssl"
    SERVER = "server"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class ProxyState:
    proxy_url: str
    failure_count: int = 0
    last_failure_type: ProxyFailureType | None = None
    last_failed_at: datetime | None = None
    soft_ban_until: datetime | None = None
    is_hard_banned: bool = False


@dataclass(slots=True)
class ProxySourceState:
    consecutive_failures: int = 0
    cooldown_until: datetime | None = None


class ProxyManager:
    """싱글톤 프록시 관리자."""

    _instance = None
    _initialized = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, proxy_url="https://www.sslproxies.org/"):
        if ProxyManager._initialized:
            return
        self.proxy_url = proxy_url
        self.proxies: deque[str] = deque()
        self._proxy_set: set[str] = set()
        self._proxy_states: dict[str, ProxyState] = {}
        self._failure_type_counts: Counter[ProxyFailureType] = Counter()
        self._batch_failure_type_counts: Counter[ProxyFailureType] = Counter()
        self._source_states: dict[str, ProxySourceState] = {
            self.proxy_url: ProxySourceState()
        }
        ProxyManager._initialized = True

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)

    @staticmethod
    def classify_failure(
        *,
        status_code: int | None = None,
        error: Exception | None = None,
    ) -> ProxyFailureType:
        if status_code in {403, 429, 430}:
            return ProxyFailureType.BLOCKED
        if status_code is not None and 500 <= status_code <= 599:
            return ProxyFailureType.SERVER

        if error is not None:
            message = f"{type(error).__name__}: {error}".lower()
            if any(token in message for token in ("ssl", "certificate", "tls", "verify")):
                return ProxyFailureType.SSL
            if any(
                token in message
                for token in ("connection", "connect", "disconnect", "timeout", "timed out")
            ):
                return ProxyFailureType.NETWORK
        return ProxyFailureType.UNKNOWN

    def _ensure_proxy_state(self, proxy_url: str) -> ProxyState:
        state = self._proxy_states.get(proxy_url)
        if state is None:
            state = ProxyState(proxy_url=proxy_url)
            self._proxy_states[proxy_url] = state
        return state

    def _get_source_state(self) -> ProxySourceState:
        if self.proxy_url not in self._source_states:
            self._source_states[self.proxy_url] = ProxySourceState()
        return self._source_states[self.proxy_url]

    def _is_source_on_cooldown(self) -> bool:
        state = self._get_source_state()
        return bool(state.cooldown_until and state.cooldown_until > self._now())

    def _mark_source_failure(self, reason: str) -> None:
        state = self._get_source_state()
        state.consecutive_failures += 1
        threshold = max(1, settings.PROXY_SOURCE_FAILURE_THRESHOLD)
        if state.consecutive_failures >= threshold:
            cooldown_seconds = max(1, settings.PROXY_SOURCE_COOLDOWN_SECONDS)
            state.cooldown_until = self._now() + timedelta(seconds=cooldown_seconds)
            state.consecutive_failures = 0
            logger.warning(
                "프록시 소스 쿨다운 적용: source=%s, reason=%s, cooldown_until=%s",
                self.proxy_url,
                reason,
                state.cooldown_until.isoformat(),
            )
            return
        logger.warning(
            "프록시 소스 실패 누적: source=%s, reason=%s, consecutive_failures=%s/%s",
            self.proxy_url,
            reason,
            state.consecutive_failures,
            threshold,
        )

    def _mark_source_success(self) -> None:
        state = self._get_source_state()
        state.consecutive_failures = 0
        state.cooldown_until = None

    def _extract_proxies_from_html(self, html: bytes) -> list[str]:
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("table", {"class": "table table-striped table-bordered"})
        if not table:
            logger.warning("프록시 테이블을 찾을 수 없습니다.")
            return []

        tbody = table.find("tbody")
        if tbody is None:
            logger.warning("프록시 테이블 본문을 찾을 수 없습니다.")
            return []

        rows = tbody.find_all("tr")
        proxies: list[str] = []
        seen: set[str] = set()
        skipped_invalid_rows = 0

        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 2:
                skipped_invalid_rows += 1
                continue

            host = cells[0].text.strip()
            port_text = cells[1].text.strip()
            if not host or not port_text:
                skipped_invalid_rows += 1
                continue

            try:
                ip_address(host)
                port = int(port_text)
            except ValueError:
                skipped_invalid_rows += 1
                continue

            if port < 1 or port > 65535:
                skipped_invalid_rows += 1
                continue

            proxy_url = f"http://{host}:{port}"
            if proxy_url in seen:
                continue
            seen.add(proxy_url)
            proxies.append(proxy_url)

        if skipped_invalid_rows > 0:
            logger.debug(
                "프록시 테이블 파싱 중 유효하지 않은 행 제외: skipped_invalid_rows=%s",
                skipped_invalid_rows,
            )
        return proxies

    @staticmethod
    def _is_public_proxy_endpoint(proxy_url: str) -> bool:
        parsed = urlparse(proxy_url)
        host = parsed.hostname
        if host is None:
            return False
        try:
            parsed_ip = ip_address(host)
        except ValueError:
            return False
        return parsed_ip.is_global

    def _is_proxy_healthy(self, proxy_url: str) -> bool:
        if not settings.PROXY_HEALTHCHECK_ENABLED:
            return True
        if not self._is_public_proxy_endpoint(proxy_url):
            logger.warning("비공인/비정상 프록시 엔드포인트 제외: proxy=%s", proxy_url)
            return False

        try:
            response = requests.get(
                settings.PROXY_HEALTHCHECK_URL,
                proxies={"http": proxy_url, "https": proxy_url},
                timeout=settings.PROXY_HEALTHCHECK_TIMEOUT_SECONDS,
            )
            return response.status_code < 500
        except Exception as e:
            logger.debug("프록시 헬스체크 실패: proxy=%s, error=%s", proxy_url, e)
            return False

    def fetch_proxies(self):
        """무료 프록시를 수집하여 저장."""
        if self._is_source_on_cooldown():
            source_state = self._get_source_state()
            logger.warning(
                "프록시 소스가 쿨다운 중입니다. source=%s, cooldown_until=%s",
                self.proxy_url,
                source_state.cooldown_until.isoformat() if source_state.cooldown_until else None,
            )
            return list(self.proxies)

        try:
            response = requests.get(self.proxy_url, timeout=30)
            response.raise_for_status()
            candidates = self._extract_proxies_from_html(response.content)
            if not candidates:
                self._mark_source_failure("empty_candidates")
                return list(self.proxies)

            pool_size_before = len(self._proxy_set)
            added = 0
            unhealthy = 0
            skipped_existing = 0
            skipped_hard_banned = 0
            for proxy_url in candidates:
                state = self._ensure_proxy_state(proxy_url)
                if state.is_hard_banned:
                    skipped_hard_banned += 1
                    continue
                if proxy_url in self._proxy_set:
                    skipped_existing += 1
                    continue
                if not self._is_proxy_healthy(proxy_url):
                    unhealthy += 1
                    self.record_proxy_failure(proxy_url, ProxyFailureType.NETWORK)
                    continue
                if self.register_proxy(proxy_url):
                    added += 1

            if added > 0:
                self._mark_source_success()
            else:
                self._mark_source_failure("no_healthy_proxy_added")

            metrics = self.get_metrics()
            logger.info(
                "프록시 수집 결과: candidates=%s, added=%s, unhealthy=%s, "
                "skipped_existing=%s, skipped_hard_banned=%s, pool_size_before=%s, "
                "pool_size_after=%s, active=%s, soft_banned=%s, hard_banned=%s",
                len(candidates),
                added,
                unhealthy,
                skipped_existing,
                skipped_hard_banned,
                pool_size_before,
                len(self._proxy_set),
                metrics["active_proxy_count"],
                metrics["soft_banned_count"],
                metrics["hard_banned_count"],
            )

        except Exception as e:
            self._mark_source_failure(str(e))
            logger.error(f"프록시 가져오기 실패: {e}")
        return list(self.proxies)

    def reset_proxies(self, clear_history: bool = False):
        """프록시 큐를 초기화합니다. clear_history=True일 때만 실패 이력도 초기화합니다."""
        self.proxies.clear()
        self._proxy_set.clear()
        if clear_history:
            self._proxy_states.clear()
            self._failure_type_counts.clear()
            self._batch_failure_type_counts.clear()
            self._source_states.clear()
            self._source_states[self.proxy_url] = ProxySourceState()
        logger.info("프록시 리스트 초기화 완료 (clear_history=%s)", clear_history)

    def start_batch(self) -> None:
        self._batch_failure_type_counts.clear()

    def _release_expired_soft_bans(self, *, now: datetime | None = None) -> int:
        current = now or self._now()
        released = 0
        for state in self._proxy_states.values():
            if state.soft_ban_until and state.soft_ban_until <= current:
                state.soft_ban_until = None
                released += 1
        return released

    def _has_active_soft_ban(
        self,
        state: ProxyState,
        *,
        now: datetime | None = None,
    ) -> bool:
        if state.soft_ban_until is None:
            return False
        current = now or self._now()
        return state.soft_ban_until > current

    def get_next_proxy(self) -> str | None:
        """다음 사용 가능한 프록시를 반환합니다."""
        if not self.proxies:
            logger.warning("사용 가능한 프록시가 없습니다.")
            return None

        self._release_expired_soft_bans()
        for _ in range(len(self.proxies)):
            proxy = self.proxies.popleft()
            state = self._ensure_proxy_state(proxy)
            if state.is_hard_banned:
                self._proxy_set.discard(proxy)
                logger.debug("하드 밴 프록시 제거: %s", proxy)
                continue
            if not self._has_active_soft_ban(state):
                self.proxies.append(proxy)
                return proxy
            self.proxies.append(proxy)
            logger.debug("소프트 밴 프록시 건너뛰기: %s", proxy)

        metrics = self.get_metrics()
        logger.warning(
            "사용 가능한 프록시가 없습니다. active=%s, soft_banned=%s, hard_banned=%s",
            metrics["active_proxy_count"],
            metrics["soft_banned_count"],
            metrics["hard_banned_count"],
        )
        return None

    def _remove_from_pool(self, proxy_url: str) -> None:
        if proxy_url not in self._proxy_set:
            return
        self._proxy_set.discard(proxy_url)
        self.proxies = deque(item for item in self.proxies if item != proxy_url)

    def register_proxy(self, proxy_url: str) -> bool:
        state = self._ensure_proxy_state(proxy_url)
        if state.is_hard_banned:
            return False
        if proxy_url in self._proxy_set:
            return False
        self.proxies.append(proxy_url)
        self._proxy_set.add(proxy_url)
        return True

    def record_proxy_failure(
        self,
        proxy_url: str,
        failure_type: ProxyFailureType,
        failed_at: datetime | None = None,
    ) -> ProxyState:
        state = self._ensure_proxy_state(proxy_url)
        timestamp = failed_at or self._now()

        state.failure_count += 1
        state.last_failure_type = failure_type
        state.last_failed_at = timestamp
        self._failure_type_counts[failure_type] += 1
        self._batch_failure_type_counts[failure_type] += 1

        soft_threshold = max(1, settings.PROXY_SOFT_BAN_FAILURE_THRESHOLD)
        hard_threshold = max(soft_threshold, settings.PROXY_HARD_BAN_FAILURE_THRESHOLD)

        if state.failure_count >= hard_threshold:
            state.is_hard_banned = True
            state.soft_ban_until = None
            self._remove_from_pool(proxy_url)
            logger.warning(
                "프록시 하드 밴 적용: proxy=%s, failure_count=%s, failure_type=%s",
                proxy_url,
                state.failure_count,
                failure_type.value,
            )
            return state

        if state.failure_count >= soft_threshold:
            ttl_seconds = max(1, settings.PROXY_SOFT_BAN_TTL_SECONDS)
            state.soft_ban_until = timestamp + timedelta(seconds=ttl_seconds)
            logger.info(
                "프록시 소프트 밴 적용: proxy=%s, failure_count=%s, until=%s, failure_type=%s",
                proxy_url,
                state.failure_count,
                state.soft_ban_until.isoformat(),
                failure_type.value,
            )
            return state

        logger.info(
            "프록시 실패 누적: proxy=%s, failure_count=%s, failure_type=%s",
            proxy_url,
            state.failure_count,
            failure_type.value,
        )
        return state

    def rehabilitate_proxy_history(
        self,
        *,
        failure_types: set[ProxyFailureType],
        reason: str,
    ) -> dict[str, int]:
        summary = {
            "reset": 0,
            "released_soft_bans": 0,
            "released_hard_bans": 0,
            "requeued": 0,
        }
        if not failure_types:
            return summary

        for proxy_url, state in self._proxy_states.items():
            if state.last_failure_type not in failure_types:
                continue
            if (
                state.failure_count == 0
                and state.soft_ban_until is None
                and not state.is_hard_banned
            ):
                continue

            if state.soft_ban_until is not None:
                summary["released_soft_bans"] += 1
            if state.is_hard_banned:
                summary["released_hard_bans"] += 1

            state.failure_count = 0
            state.last_failure_type = None
            state.last_failed_at = None
            state.soft_ban_until = None
            state.is_hard_banned = False
            summary["reset"] += 1

            if self.register_proxy(proxy_url):
                summary["requeued"] += 1

        logger.info(
            "프록시 이력 재정비: reason=%s, failure_types=%s, summary=%s",
            reason,
            sorted(failure_type.value for failure_type in failure_types),
            summary,
        )
        return summary

    def remove_proxy(
        self,
        proxy_url: str,
        failure_type: ProxyFailureType = ProxyFailureType.UNKNOWN,
    ) -> ProxyState:
        """하위 호환용 메서드. 실패 이력 누적 기반 밴 정책을 적용합니다."""
        return self.record_proxy_failure(proxy_url, failure_type)

    def record_proxy_success(self, proxy_url: str) -> ProxyState:
        state = self._ensure_proxy_state(proxy_url)
        if state.is_hard_banned:
            return state

        decay = max(1, settings.PROXY_SUCCESS_DECAY)
        state.failure_count = max(0, state.failure_count - decay)
        if state.failure_count < max(1, settings.PROXY_SOFT_BAN_FAILURE_THRESHOLD):
            state.soft_ban_until = None
        if state.failure_count == 0:
            state.last_failure_type = None
            state.last_failed_at = None
        return state

    def get_failure_backoff_seconds(self, failure_type: ProxyFailureType) -> float:
        mapping = {
            ProxyFailureType.BLOCKED: settings.PROXY_BACKOFF_BLOCKED_SECONDS,
            ProxyFailureType.NETWORK: settings.PROXY_BACKOFF_NETWORK_SECONDS,
            ProxyFailureType.SSL: settings.PROXY_BACKOFF_SSL_SECONDS,
            ProxyFailureType.SERVER: settings.PROXY_BACKOFF_SERVER_SECONDS,
            ProxyFailureType.UNKNOWN: settings.PROXY_BACKOFF_UNKNOWN_SECONDS,
        }
        backoff = float(mapping.get(failure_type, settings.PROXY_BACKOFF_UNKNOWN_SECONDS))
        return max(0.0, backoff)

    def get_metrics(self) -> dict[str, int]:
        now = self._now()
        soft_banned_count = 0
        hard_banned_count = 0
        for state in self._proxy_states.values():
            if state.is_hard_banned:
                hard_banned_count += 1
                continue
            if self._has_active_soft_ban(state, now=now):
                soft_banned_count += 1

        active_proxy_count = 0
        for proxy_url in self._proxy_set:
            state = self._ensure_proxy_state(proxy_url)
            if state.is_hard_banned:
                continue
            if self._has_active_soft_ban(state, now=now):
                continue
            active_proxy_count += 1

        return {
            "active_proxy_count": active_proxy_count,
            "soft_banned_count": soft_banned_count,
            "hard_banned_count": hard_banned_count,
        }

    def get_failure_rates(self, *, batch_only: bool = False) -> dict[str, float]:
        counts = self._batch_failure_type_counts if batch_only else self._failure_type_counts
        total = sum(counts.values())
        if total == 0:
            return {failure_type.value: 0.0 for failure_type in ProxyFailureType}
        return {
            failure_type.value: counts.get(failure_type, 0) / total
            for failure_type in ProxyFailureType
        }

    def log_metrics(self, context: str) -> None:
        metrics = self.get_metrics()
        batch_failure_rates = self.get_failure_rates(batch_only=True)
        logger.info(
            "[METRIC] proxy_pool context=%s active_proxy_count=%s "
            "soft_banned_count=%s hard_banned_count=%s batch_failure_rates=%s",
            context,
            metrics["active_proxy_count"],
            metrics["soft_banned_count"],
            metrics["hard_banned_count"],
            batch_failure_rates,
        )

    def get_available_proxy_count(self) -> int:
        return self.get_metrics()["active_proxy_count"]

    def ensure_min_available_proxies(self, min_available: int | None = None) -> bool:
        required = max(1, min_available or settings.MIN_AVAILABLE_PROXIES)
        available = self.get_available_proxy_count()
        if available >= required:
            return True

        logger.warning(
            "가용 프록시 부족 감지: available=%s, required=%s. 보강 절차를 시작합니다.",
            available,
            required,
        )
        attempts = max(1, settings.PROXY_REPLENISH_ATTEMPTS)
        for attempt in range(1, attempts + 1):
            logger.info("프록시 보강 시도 %s/%s", attempt, attempts)
            self.fetch_proxies()
            available = self.get_available_proxy_count()
            if available >= required:
                logger.info(
                    "프록시 보강 성공: available=%s, required=%s",
                    available,
                    required,
                )
                self.log_metrics("replenish_success")
                return True

        logger.error(
            "프록시 보강 실패: available=%s, required=%s, attempts=%s",
            available,
            required,
            attempts,
        )
        self.log_metrics("replenish_failed")
        return False

    def get_proxy_state(self, proxy_url: str) -> ProxyState | None:
        return self._proxy_states.get(proxy_url)
