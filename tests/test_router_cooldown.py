"""Health-driven demotion tests.

Verifies that the router refuses to route to providers placed in a hard
cooldown by the adaptive route-pressure tracker. Without these checks a
broken provider (wrong model, expired token, persistent 4xx body) would
be re-selected on every request as long as it sits at the top of a
`prefer_providers` list — burning the user's request budget for the
entire cooldown window. See faigate/adaptation.py for the cooldown
classification, faigate/router.py:_provider_in_hard_cooldown for the
routing-time enforcement.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from faigate.adaptation import RoutePressure
from faigate.config import load_config
from faigate.router import Router, _RoutingContext


def _write_two_provider_config(tmp_path: Path) -> Path:
    body = """
server:
  host: "127.0.0.1"
  port: 8090
providers:
  broken-provider:
    backend: openai-compat
    base_url: "https://api.example.com/v1"
    api_key: "secret"
    model: "broken-model"
    capabilities:
      cost_tier: standard
      latency_tier: balanced
    lane:
      family: example
      name: broken-lane
      canonical_model: example/broken
      route_type: direct
  healthy-provider:
    backend: openai-compat
    base_url: "https://api.example.com/v1"
    api_key: "secret"
    model: "healthy-model"
    capabilities:
      cost_tier: standard
      latency_tier: balanced
    lane:
      family: example
      name: healthy-lane
      canonical_model: example/healthy
      route_type: direct
fallback_chain:
  - broken-provider
  - healthy-provider
metrics:
  enabled: false
"""
    path = tmp_path / "config.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def _build_ctx(
    cfg,
    *,
    runtime_state: dict[str, dict] | None = None,
    health: dict[str, dict] | None = None,
) -> _RoutingContext:
    """Construct a minimal RoutingContext with everything routing needs."""
    providers = cfg.providers
    return _RoutingContext(
        system_prompt="",
        last_user_message="hi",
        full_text="hi",
        total_tokens=4,
        stable_prefix_tokens=0,
        requested_output_tokens=8,
        total_requested_tokens=12,
        requested_image_outputs=0,
        requested_image_side_px=0,
        requested_image_size="",
        requested_image_policy="",
        required_capability="",
        cache_preference="",
        model_requested="auto",
        has_tools=False,
        client_profile="generic",
        profile_hints={},
        hook_hints={},
        applied_hooks=[],
        headers={},
        provider_health=health or {name: {"healthy": True} for name in providers},
        provider_runtime_state=runtime_state or {},
        providers=providers,
        request_insights={},
    )


@pytest.fixture
def two_provider_router(tmp_path):
    cfg = load_config(_write_two_provider_config(tmp_path))
    return Router(cfg), cfg


def test_provider_in_hard_cooldown_reads_request_blocked_flag(two_provider_router):
    """The helper should mirror RoutePressure.request_blocked exactly."""
    router, cfg = two_provider_router

    # Build a real RoutePressure that will trigger model-unavailable cooldown.
    pressure = RoutePressure(provider_name="broken-provider")
    pressure.record_failure("HTTP 400: model not found")
    snapshot = pressure.to_dict()
    assert snapshot["request_blocked"] is True
    assert snapshot["last_issue_type"] == "model-unavailable"

    ctx = _build_ctx(cfg, runtime_state={"broken-provider": snapshot})

    blocked, runtime_state = router._provider_in_hard_cooldown("broken-provider", ctx)
    assert blocked is True
    assert runtime_state["last_issue_type"] == "model-unavailable"

    # Healthy provider is not in any state -> not blocked
    blocked_clean, _ = router._provider_in_hard_cooldown("healthy-provider", ctx)
    assert blocked_clean is False


def test_provider_in_hard_cooldown_handles_missing_context(two_provider_router):
    router, _ = two_provider_router
    blocked, runtime_state = router._provider_in_hard_cooldown("broken-provider", None)
    assert blocked is False
    assert runtime_state == {}


def test_select_policy_provider_skips_hard_cooldown_even_if_first_in_prefer_list(two_provider_router):
    """Regression test for the openai-codex 400-loop incident.

    Before the fix, a provider sitting at the top of `prefer_providers` would
    be returned even after the adaptive tracker placed it in a hard cooldown,
    because `_select_policy_provider` only checked `provider_health.healthy`.
    The healthy flag flips back to True after a single successful probe even
    if user-facing requests are still 400ing. With the fix the cooldown'd
    provider is excluded from the candidate set entirely, so the second-best
    healthy provider wins.
    """
    router, cfg = two_provider_router

    pressure = RoutePressure(provider_name="broken-provider")
    pressure.record_failure("HTTP 400: model not found")
    runtime_state = {"broken-provider": pressure.to_dict()}

    ctx = _build_ctx(cfg, runtime_state=runtime_state)

    # broken-provider is FIRST in prefer_providers — without the cooldown
    # exclusion the router would happily pick it even though it's blocked.
    selected, ranking = router._select_policy_provider(
        {"prefer_providers": ["broken-provider", "healthy-provider"]},
        ctx,
    )

    assert selected == "healthy-provider"
    assert all(entry["provider"] != "broken-provider" for entry in ranking)


def test_select_policy_provider_recovers_after_cooldown_window_expires(two_provider_router, monkeypatch):
    """Once the cooldown window elapses the provider is auto-eligible again.

    We don't fast-forward time; instead we synthesize a runtime_state
    dictionary that reflects "cooldown already passed" — request_blocked
    False, no remaining seconds — to verify the gate re-opens cleanly.
    """
    router, cfg = two_provider_router

    expired_state = {
        "last_issue_type": "model-unavailable",
        "request_blocked": False,
        "cooldown_remaining_s": 0,
        "window_state": "clear",
        "penalty": 0,
    }

    ctx = _build_ctx(cfg, runtime_state={"broken-provider": expired_state})

    selected, _ = router._select_policy_provider(
        {"prefer_providers": ["broken-provider", "healthy-provider"]},
        ctx,
    )

    assert selected == "broken-provider"


def test_validate_health_falls_through_when_primary_in_cooldown(two_provider_router):
    """A `RoutingDecision` pointing at a cooldown'd primary should fall to the
    fallback chain, with the rule_name suffixed `→fallback` and reason text
    naming the cooldown reason for observability."""
    router, cfg = two_provider_router

    pressure = RoutePressure(provider_name="broken-provider")
    pressure.record_failure("HTTP 400: model not found")
    runtime_state = {"broken-provider": pressure.to_dict()}

    ctx = _build_ctx(cfg, runtime_state=runtime_state)

    # Forge a decision pointing at the cooldown'd primary.
    from faigate.router import RoutingDecision

    primary_decision = RoutingDecision(
        provider_name="broken-provider",
        layer="hook",
        rule_name="request-hooks",
        confidence=0.7,
        reason="hook selected primary",
    )

    final = router._validate_health(primary_decision, ctx)

    assert final.provider_name == "healthy-provider"
    assert final.rule_name.endswith("→fallback")
    assert "cooldown" in final.reason
    assert "model-unavailable" in final.reason
