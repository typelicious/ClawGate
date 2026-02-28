"""Tests for config env expansion."""

from pathlib import Path

from clawgate.config import load_config


def test_metrics_db_path_defaults_when_env_missing(monkeypatch):
    monkeypatch.delenv("CLAWGATE_DB_PATH", raising=False)
    cfg = load_config(Path(__file__).parent.parent / "config.yaml")
    assert cfg.metrics["db_path"] == "./clawgate.db"


def test_metrics_db_path_uses_env_override(monkeypatch):
    monkeypatch.setenv("CLAWGATE_DB_PATH", "/var/lib/clawgate/test.db")
    cfg = load_config(Path(__file__).parent.parent / "config.yaml")
    assert cfg.metrics["db_path"] == "/var/lib/clawgate/test.db"
