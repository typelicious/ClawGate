"""Unit tests for faigate circuit breaker state machine."""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path

from faigate.breakers import (
    Breaker,
    BreakerConfig,
    BreakerRegistry,
    CircuitState,
    breaker_registry,
)


class TestBreakerConfig:
    def test_defaults(self):
        cfg = BreakerConfig()
        assert cfg.failure_threshold == 3
        assert cfg.failure_window_s == 60
        assert cfg.cooldown_s == 30
        assert cfg.jitter_s == 5

    def test_custom(self):
        cfg = BreakerConfig(failure_threshold=5, failure_window_s=120, cooldown_s=60, jitter_s=10)
        assert cfg.failure_threshold == 5
        assert cfg.failure_window_s == 120
        assert cfg.cooldown_s == 60
        assert cfg.jitter_s == 10

    def test_from_provider_cfg(self):
        cfg = BreakerConfig.from_provider_cfg({"failure_threshold": 5, "cooldown_s": 45})
        assert cfg.failure_threshold == 5
        assert cfg.cooldown_s == 45
        assert cfg.failure_window_s == 60

    def test_from_provider_cfg_none(self):
        cfg = BreakerConfig.from_provider_cfg(None)
        assert cfg.failure_threshold == 3
        assert cfg.cooldown_s == 30


class TestBreakerBasic:
    def test_new_breaker_is_closed(self):
        b = Breaker(provider_name="test")
        assert b.state == CircuitState.CLOSED
        assert b.allow_request() is True
        assert b.failure_count == 0

    def test_three_failures_opens_circuit(self):
        b = Breaker(provider_name="test")
        b.record_failure("err1")
        assert b.state == CircuitState.CLOSED
        b.record_failure("err2")
        assert b.state == CircuitState.CLOSED
        b.record_failure("err3")
        assert b.state == CircuitState.OPEN
        assert b.allow_request() is False

    def test_single_failure_does_not_open(self):
        b = Breaker(provider_name="test")
        b.record_failure("err")
        assert b.state == CircuitState.CLOSED
        assert b.allow_request() is True

    def test_open_blocks_requests(self):
        b = Breaker(provider_name="test")
        for i in range(3):
            b.record_failure(f"err {i}")
        assert b.state == CircuitState.OPEN
        assert b.allow_request() is False

    def test_record_success_while_closed_resets_count(self):
        b = Breaker(provider_name="test")
        b.record_failure("err 1")
        b.record_failure("err 2")
        assert b.failure_count == 2
        b.record_success()
        assert b.failure_count == 0
        assert b.state == CircuitState.CLOSED

    def test_custom_threshold(self):
        cfg = BreakerConfig(failure_threshold=5)
        b = Breaker(provider_name="test", config=cfg)
        for i in range(4):
            b.record_failure(f"err {i}")
        assert b.state == CircuitState.CLOSED
        b.record_failure("err 5")
        assert b.state == CircuitState.OPEN

    def test_force_closed(self):
        b = Breaker(provider_name="test")
        for i in range(3):
            b.record_failure(f"err {i}")
        assert b.state == CircuitState.OPEN
        b.force_closed()
        assert b.state == CircuitState.CLOSED
        assert b.failure_count == 0
        assert b.allow_request() is True

    def test_last_failure_error_stored(self):
        b = Breaker(provider_name="test")
        b.record_failure("connection refused")
        assert b.last_failure_error == "connection refused"
        b.record_failure("timeout")
        assert b.last_failure_error == "timeout"

    def test_to_dict(self):
        b = Breaker(provider_name="test")
        d = b.to_dict()
        assert d["provider"] == "test"
        assert d["state"] == "CLOSED"
        assert d["failure_count"] == 0


class TestBreakerHalfOpen:
    def test_cooldown_expiry_transitions_to_half_open(self):
        b = Breaker(provider_name="test")
        for i in range(3):
            b.record_failure(f"err {i}")
        assert b.state == CircuitState.OPEN
        b.cooldown_until = time.time() - 1
        assert b.allow_request() is True
        assert b.state == CircuitState.HALF_OPEN

    def test_half_open_probe_success_closes(self):
        b = Breaker(provider_name="test")
        for i in range(3):
            b.record_failure(f"err {i}")
        b.cooldown_until = time.time() - 1
        b.allow_request()
        assert b.state == CircuitState.HALF_OPEN
        b.record_success()
        assert b.state == CircuitState.CLOSED
        assert b.failure_count == 0

    def test_half_open_probe_failure_reopens(self):
        b = Breaker(provider_name="test")
        for i in range(3):
            b.record_failure(f"err {i}")
        b.cooldown_until = time.time() - 1
        b.allow_request()
        assert b.state == CircuitState.HALF_OPEN
        b.record_failure("probe failed")
        assert b.state == CircuitState.OPEN

    def test_record_success_while_open_noop(self):
        b = Breaker(provider_name="test")
        for i in range(3):
            b.record_failure(f"err {i}")
        assert b.state == CircuitState.OPEN
        b.record_success()
        assert b.state == CircuitState.OPEN


class TestBreakerRegistry:
    def teardown_method(self):
        breaker_registry._breakers.clear()

    def test_get_or_create_same_breaker(self):
        b1 = breaker_registry.get_or_create("test-provider")
        b2 = breaker_registry.get_or_create("test-provider")
        assert b1 is b2

    def test_get_or_create_different_providers(self):
        b1 = breaker_registry.get_or_create("provider-a")
        b2 = breaker_registry.get_or_create("provider-b")
        assert b1 is not b2

    def test_get_nonexistent(self):
        assert breaker_registry.get("nonexistent") is None

    def test_get_existing(self):
        breaker_registry.get_or_create("exists")
        assert breaker_registry.get("exists") is not None

    def test_force_closed(self):
        b = breaker_registry.get_or_create("reset-me")
        for i in range(3):
            b.record_failure(f"err {i}")
        assert b.state == CircuitState.OPEN
        assert breaker_registry.force_closed("reset-me") is True
        assert b.state == CircuitState.CLOSED

    def test_force_closed_nonexistent(self):
        assert breaker_registry.force_closed("nonexistent") is False

    def test_all_states(self):
        breaker_registry._breakers.clear()
        b = breaker_registry.get_or_create("snap")
        b.record_failure("fail")
        states = breaker_registry.all_states()
        assert "snap" in states
        assert states["snap"]["state"] == "CLOSED"
        assert states["snap"]["failure_count"] == 1


class TestBreakerPersistence:
    def test_configure_persistence(self, tmp_path: Path):
        db_path = str(tmp_path / "test.db")
        reg = BreakerRegistry()
        reg.configure_persistence(db_path)

        b = reg.get_or_create("persist")
        for i in range(3):
            b.record_failure(f"err {i}")
        assert b.state == CircuitState.OPEN

        reg.persist_all()

        reg2 = BreakerRegistry()
        reg2.configure_persistence(db_path)
        b2 = reg2.get_or_create("persist")
        assert b2.failure_count == 3
        assert b2.state in (CircuitState.OPEN, CircuitState.HALF_OPEN)

    def test_db_has_correct_state(self, tmp_path: Path):
        db_path = str(tmp_path / "test_save.db")
        reg = BreakerRegistry()
        reg.configure_persistence(db_path)

        b = reg.get_or_create("db-test")
        for i in range(3):
            b.record_failure(f"err {i}")
        reg.persist_all()

        conn = sqlite3.connect(db_path)
        row = conn.execute(
            "SELECT state, failure_count FROM circuit_breakers WHERE provider = ?",
            ("db-test",),
        ).fetchone()
        conn.close()
        assert row is not None
        assert row[0] == "OPEN"
        assert row[1] == 3
