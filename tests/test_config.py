"""Tests for config safe DB path resolution and env expansion."""

from pathlib import Path

from clawgate.config import _safe_db_path, load_config

# ── _safe_db_path unit tests ──────────────────────────────────────────────────


def test_safe_db_path_env_var_wins(monkeypatch):
    """CLAWGATE_DB_PATH env var always takes priority."""
    monkeypatch.setenv("CLAWGATE_DB_PATH", "/custom/path/clawgate.db")
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    assert _safe_db_path() == "/custom/path/clawgate.db"


def test_safe_db_path_env_var_over_configured(monkeypatch):
    """Env var wins even when a configured path is provided."""
    monkeypatch.setenv("CLAWGATE_DB_PATH", "/env/clawgate.db")
    assert _safe_db_path("/configured/clawgate.db") == "/env/clawgate.db"


def test_safe_db_path_rejects_dot_slash(monkeypatch):
    """./clawgate.db must never be returned — it would pollute the repo."""
    monkeypatch.delenv("CLAWGATE_DB_PATH", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    result = _safe_db_path("./clawgate.db")
    assert not result.startswith("./"), f"unsafe path returned: {result}"
    assert "clawgate.db" in result


def test_safe_db_path_rejects_bare_name(monkeypatch):
    """Bare 'clawgate.db' (relative) must also be rejected."""
    monkeypatch.delenv("CLAWGATE_DB_PATH", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    result = _safe_db_path("clawgate.db")
    assert result != "clawgate.db"
    assert result.startswith("/")


def test_safe_db_path_accepts_absolute_configured(monkeypatch):
    """An absolute path in config.yaml is used as-is."""
    monkeypatch.delenv("CLAWGATE_DB_PATH", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    assert _safe_db_path("/var/lib/clawgate/clawgate.db") == "/var/lib/clawgate/clawgate.db"


def test_safe_db_path_xdg(monkeypatch):
    """XDG_DATA_HOME is used when no env/configured path is set."""
    monkeypatch.delenv("CLAWGATE_DB_PATH", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", "/xdg/data")
    result = _safe_db_path()
    assert result == "/xdg/data/clawgate/clawgate.db"


def test_safe_db_path_home_fallback(monkeypatch):
    """Falls back to ~/.local/share/clawgate/clawgate.db when nothing else is set."""
    monkeypatch.delenv("CLAWGATE_DB_PATH", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    result = _safe_db_path()
    assert result.endswith("/.local/share/clawgate/clawgate.db")
    assert result.startswith("/")


# ── Config.metrics integration ────────────────────────────────────────────────


def test_metrics_db_path_uses_env_override(monkeypatch):
    """CLAWGATE_DB_PATH env var is reflected in cfg.metrics['db_path']."""
    monkeypatch.setenv("CLAWGATE_DB_PATH", "/var/lib/clawgate/test.db")
    cfg = load_config(Path(__file__).parent.parent / "config.yaml")
    assert cfg.metrics["db_path"] == "/var/lib/clawgate/test.db"


def test_metrics_db_path_never_dot_slash(monkeypatch):
    """cfg.metrics['db_path'] must never start with './' regardless of config.yaml content."""
    monkeypatch.delenv("CLAWGATE_DB_PATH", raising=False)
    monkeypatch.delenv("XDG_DATA_HOME", raising=False)
    cfg = load_config(Path(__file__).parent.parent / "config.yaml")
    db_path = cfg.metrics["db_path"]
    assert not db_path.startswith("./"), f"unsafe db_path in metrics: {db_path}"
    assert db_path.startswith("/"), f"expected absolute path, got: {db_path}"
