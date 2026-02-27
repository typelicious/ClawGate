"""Configuration loader with environment variable expansion."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


def _expand_env(value: str) -> str:
    """Expand ${VAR} and ${VAR:-default} patterns in a string."""

    def _replace(m: re.Match) -> str:
        var = m.group(1)
        if ":-" in var:
            name, default = var.split(":-", 1)
            return os.environ.get(name, default)
        return os.environ.get(var, m.group(0))

    return re.sub(r"\$\{([^}]+)}", _replace, value)


def _walk_expand(obj: Any) -> Any:
    """Recursively expand env vars in all string values."""
    if isinstance(obj, str):
        return _expand_env(obj)
    if isinstance(obj, dict):
        return {k: _walk_expand(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_walk_expand(v) for v in obj]
    return obj


class Config:
    """Holds the parsed and expanded configuration."""

    def __init__(self, data: dict):
        self._data = data

    # ── Accessors ──────────────────────────────────────────────

    @property
    def server(self) -> dict:
        return self._data.get("server", {})

    @property
    def providers(self) -> dict:
        return self._data.get("providers", {})

    @property
    def fallback_chain(self) -> list[str]:
        return self._data.get("fallback_chain", [])

    @property
    def static_rules(self) -> dict:
        return self._data.get("static_rules", {"enabled": False, "rules": []})

    @property
    def heuristic_rules(self) -> dict:
        return self._data.get("heuristic_rules", {"enabled": False, "rules": []})

    @property
    def llm_classifier(self) -> dict:
        return self._data.get("llm_classifier", {"enabled": False})

    @property
    def health(self) -> dict:
        return self._data.get("health", {})

    @property
    def metrics(self) -> dict:
        return self._data.get("metrics", {"enabled": False})

    def provider(self, name: str) -> dict | None:
        return self.providers.get(name)


def load_config(path: str | Path | None = None) -> Config:
    """Load config.yaml, expand env vars, return Config object."""
    load_dotenv()

    if path is None:
        # Look next to the package, then cwd
        candidates = [
            Path(__file__).resolve().parent.parent / "config.yaml",
            Path.cwd() / "config.yaml",
        ]
        for c in candidates:
            if c.exists():
                path = c
                break
        else:
            raise FileNotFoundError("config.yaml not found")

    path = Path(path)
    with path.open() as f:
        raw = yaml.safe_load(f)

    expanded = _walk_expand(raw)
    return Config(expanded)
