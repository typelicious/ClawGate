"""Per-provider circuit breaker state machine with SQLite persistence."""

from __future__ import annotations

import enum
import logging
import random
import sqlite3
import time
from dataclasses import dataclass, field

logger = logging.getLogger("faigate.breakers")


class CircuitState(enum.Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

    def __str__(self) -> str:
        return self.value


DEFAULT_FAILURE_WINDOW_S = 60
DEFAULT_FAILURE_THRESHOLD = 3
DEFAULT_COOLDOWN_S = 30
DEFAULT_JITTER_S = 5.0


@dataclass
class BreakerConfig:
    failure_window_s: float = DEFAULT_FAILURE_WINDOW_S
    failure_threshold: int = DEFAULT_FAILURE_THRESHOLD
    cooldown_s: float = DEFAULT_COOLDOWN_S
    jitter_s: float = DEFAULT_JITTER_S

    @classmethod
    def from_provider_cfg(cls, cfg: dict | None) -> BreakerConfig:
        if not cfg:
            return cls()
        return cls(
            failure_window_s=float(cfg.get("failure_window_s", DEFAULT_FAILURE_WINDOW_S)),
            failure_threshold=int(cfg.get("failure_threshold", DEFAULT_FAILURE_THRESHOLD)),
            cooldown_s=float(cfg.get("cooldown_s", DEFAULT_COOLDOWN_S)),
            jitter_s=float(cfg.get("jitter_s", DEFAULT_JITTER_S)),
        )


@dataclass
class Breaker:
    provider_name: str
    config: BreakerConfig = field(default_factory=BreakerConfig)
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    failure_timestamps: list[float] = field(default_factory=list)
    opened_at: float = 0.0
    cooldown_until: float = 0.0
    half_open_probes: int = 0
    last_success_at: float = 0.0
    last_failure_at: float = 0.0
    last_failure_error: str = ""

    @property
    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        if self.state != CircuitState.OPEN:
            return False
        if time.time() >= self.cooldown_until:
            return False
        return True

    @property
    def cooldown_remaining_s(self) -> float:
        return max(0.0, self.cooldown_until - time.time())

    def record_success(self) -> None:
        now = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.CLOSED
            self.failure_count = 0
            self.failure_timestamps.clear()
            self.half_open_probes = 0
            self.last_failure_error = ""
            self.opened_at = 0.0
            self.cooldown_until = 0.0
            logger.info("Breaker %s: HALF_OPEN → CLOSED (probe succeeded)", self.provider_name)
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
            self.failure_timestamps.clear()
        self.last_success_at = now

    def record_failure(self, error: str = "") -> None:
        now = time.time()
        self.last_failure_at = now
        self.last_failure_error = error

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            self.opened_at = now
            jitter = random.uniform(-self.config.jitter_s, self.config.jitter_s)
            self.cooldown_until = now + self.config.cooldown_s + jitter
            self.half_open_probes = 0
            logger.warning(
                "Breaker %s: HALF_OPEN → OPEN (probe failed): %s",
                self.provider_name,
                error,
            )
            return

        self.failure_timestamps.append(now)
        cutoff = now - self.config.failure_window_s
        self.failure_timestamps = [t for t in self.failure_timestamps if t >= cutoff]
        self.failure_count = len(self.failure_timestamps)

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            self.opened_at = now
            jitter = random.uniform(-self.config.jitter_s, self.config.jitter_s)
            self.cooldown_until = now + self.config.cooldown_s + jitter
            logger.warning(
                "Breaker %s: CLOSED → OPEN (%d failures in %.0fs): %s",
                self.provider_name,
                self.failure_count,
                self.config.failure_window_s,
                error,
            )

    def allow_request(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            if time.time() >= self.cooldown_until:
                self.state = CircuitState.HALF_OPEN
                self.half_open_probes = 0
                logger.info("Breaker %s: OPEN → HALF_OPEN (cooldown elapsed)", self.provider_name)
                return True
            return False
        if self.state == CircuitState.HALF_OPEN:
            return True
        return True

    def force_closed(self) -> None:
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.failure_timestamps.clear()
        self.half_open_probes = 0
        self.opened_at = 0.0
        self.cooldown_until = 0.0
        self.last_failure_error = ""
        logger.info("Breaker %s: force-reset to CLOSED", self.provider_name)

    def to_dict(self) -> dict:
        return {
            "provider": self.provider_name,
            "state": str(self.state),
            "failure_count": self.failure_count,
            "failure_window_s": self.config.failure_window_s,
            "cooldown_s": self.config.cooldown_s,
            "cooldown_remaining_s": round(self.cooldown_remaining_s, 1),
            "opened_at": self.opened_at,
            "half_open_probes": self.half_open_probes,
            "last_success_at": self.last_success_at,
            "last_failure_at": self.last_failure_at,
            "last_failure_error": self.last_failure_error,
        }


class BreakerRegistry:
    """Singleton registry of per-provider circuit breakers."""

    def __init__(self) -> None:
        self._breakers: dict[str, Breaker] = {}
        self._db_path: str | None = None

    def configure_persistence(self, db_path: str) -> None:
        self._db_path = db_path
        self._ensure_table()
        self.load_all()

    def get_or_create(self, provider_name: str, config_cfg: dict | None = None) -> Breaker:
        if provider_name not in self._breakers:
            breaker_config = BreakerConfig.from_provider_cfg(config_cfg)
            self._breakers[provider_name] = Breaker(
                provider_name=provider_name,
                config=breaker_config,
            )
        return self._breakers[provider_name]

    def get(self, provider_name: str) -> Breaker | None:
        return self._breakers.get(provider_name)

    def all_states(self) -> dict[str, dict]:
        return {name: b.to_dict() for name, b in self._breakers.items()}

    def force_closed(self, provider_name: str) -> bool:
        breaker = self._breakers.get(provider_name)
        if breaker is None:
            return False
        breaker.force_closed()
        self._save(breaker)
        return True

    def _save(self, breaker: Breaker) -> None:
        if not self._db_path:
            return
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    """INSERT OR REPLACE INTO circuit_breakers
                       (provider, state, failure_count, opened_at, half_open_probes, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        breaker.provider_name,
                        str(breaker.state),
                        breaker.failure_count,
                        breaker.opened_at,
                        breaker.half_open_probes,
                        time.time(),
                    ),
                )
        except Exception:
            logger.exception("Failed to persist breaker state for %s", breaker.provider_name)

    def persist_all(self) -> None:
        for breaker in self._breakers.values():
            self._save(breaker)

    def load_all(self) -> None:
        if not self._db_path:
            return
        try:
            with sqlite3.connect(self._db_path) as conn:
                rows = conn.execute(
                    "SELECT provider, state, failure_count, opened_at, "
                    "half_open_probes, updated_at FROM circuit_breakers"
                ).fetchall()
        except sqlite3.OperationalError:
            self._ensure_table()
            return
        now = time.time()
        for row in rows:
            provider, state_str, failure_count, opened_at, half_open_probes, _updated_at = row
            breaker = self.get_or_create(provider)
            breaker.failure_count = failure_count
            breaker.opened_at = opened_at
            breaker.half_open_probes = half_open_probes
            if state_str == "OPEN":
                breaker.state = CircuitState.OPEN
                breaker.cooldown_until = (
                    opened_at + breaker.config.cooldown_s if opened_at else now + breaker.config.cooldown_s
                )
                if now >= breaker.cooldown_until:
                    breaker.state = CircuitState.HALF_OPEN
                    logger.info("Breaker %s: restored OPEN → HALF_OPEN (cooldown elapsed)", provider)
            elif state_str == "HALF_OPEN":
                breaker.state = CircuitState.HALF_OPEN
            logger.debug("Breaker %s: loaded state %s from persistence", provider, state_str)

    def _ensure_table(self) -> None:
        if not self._db_path:
            return
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    """CREATE TABLE IF NOT EXISTS circuit_breakers (
                        provider TEXT PRIMARY KEY,
                        state TEXT NOT NULL DEFAULT 'CLOSED',
                        failure_count INTEGER NOT NULL DEFAULT 0,
                        opened_at REAL NOT NULL DEFAULT 0.0,
                        half_open_probes INTEGER NOT NULL DEFAULT 0,
                        updated_at REAL NOT NULL DEFAULT 0.0
                    )"""
                )
        except Exception:
            logger.exception("Failed to create circuit_breakers table")


breaker_registry = BreakerRegistry()
