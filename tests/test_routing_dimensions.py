"""Tests for context-window, provider-limit, and cache-aware routing."""

from pathlib import Path

import pytest

from foundrygate.config import ConfigError, load_config
from foundrygate.router import Router


def _write_config(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(body)
    return path


@pytest.mark.asyncio
async def test_profile_prefers_cache_and_context_fit(tmp_path):
    cfg = load_config(
        _write_config(
            tmp_path,
            """
server:
  host: "127.0.0.1"
  port: 8090
providers:
  cheap-small:
    backend: openai-compat
    base_url: "https://api.example.com/v1"
    api_key: "secret"
    model: "cheap-chat"
    tier: default
    context_window: 4096
    limits:
      max_input_tokens: 2048
    cache:
      mode: none
  cached-large:
    backend: openai-compat
    base_url: "https://api.example.com/v1"
    api_key: "secret"
    model: "cached-chat"
    tier: default
    context_window: 131072
    limits:
      max_input_tokens: 65536
    cache:
      mode: implicit
      read_discount: true
client_profiles:
  enabled: true
  default: generic
  profiles:
    generic:
      prefer_tiers: ["default"]
static_rules:
  enabled: false
  rules: []
heuristic_rules:
  enabled: false
  rules: []
fallback_chain:
  - cached-large
metrics:
  enabled: false
""",
        )
    )
    router = Router(cfg)
    long_system = "stable prefix " * 80

    decision = await router.route(
        [
            {"role": "system", "content": long_system},
            {"role": "user", "content": "Summarize this long request."},
        ],
        model_requested="auto",
        requested_max_tokens=512,
        client_profile="generic",
        profile_hints=cfg.client_profiles["profiles"]["generic"],
        headers={"x-foundrygate-cache": "prefer-cache"},
    )

    assert decision.layer == "profile"
    assert decision.provider_name == "cached-large"


@pytest.mark.asyncio
async def test_unfit_provider_falls_back_to_context_fit_provider(tmp_path):
    cfg = load_config(
        _write_config(
            tmp_path,
            """
server:
  host: "127.0.0.1"
  port: 8090
providers:
  tiny-reasoner:
    backend: openai-compat
    base_url: "https://api.example.com/v1"
    api_key: "secret"
    model: "tiny-reasoner"
    tier: reasoning
    context_window: 4096
    limits:
      max_input_tokens: 1024
  roomy-default:
    backend: openai-compat
    base_url: "https://api.example.com/v1"
    api_key: "secret"
    model: "roomy-chat"
    tier: default
    context_window: 65536
    limits:
      max_input_tokens: 32768
static_rules:
  enabled: false
  rules: []
heuristic_rules:
  enabled: true
  rules:
    - name: default-route
      match:
        fallthrough: true
      route_to: tiny-reasoner
fallback_chain:
  - roomy-default
metrics:
  enabled: false
""",
        )
    )
    router = Router(cfg)
    huge_user = "context " * 700

    decision = await router.route(
        [{"role": "user", "content": huge_user}],
        model_requested="auto",
        requested_max_tokens=256,
        client_profile="generic",
        headers={},
        provider_health={
            "tiny-reasoner": {"healthy": True},
            "roomy-default": {"healthy": True},
        },
    )

    assert decision.provider_name == "roomy-default"
    assert decision.rule_name.endswith("fallback")
    assert "request dimensions" in decision.reason


def test_provider_rejects_invalid_cache_mode(tmp_path):
    path = _write_config(
        tmp_path,
        """
server:
  host: "127.0.0.1"
  port: 8090
providers:
  invalid:
    backend: openai-compat
    base_url: "https://api.example.com/v1"
    api_key: "secret"
    model: "chat"
    cache:
      mode: strange
fallback_chain: []
metrics:
  enabled: false
""",
    )

    with pytest.raises(ConfigError, match="cache.mode"):
        load_config(path)
