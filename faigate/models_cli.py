"""CLI for the provider catalog updater.

Usage:
    faigate-models update            Force-refresh the cached catalog from remote.
    faigate-models update --check    Exit 0 if cache is fresh, 1 if stale, 2 on error.
    faigate-models update --diff     Show provider/model deltas vs current cache.
    faigate-models status            Print cache age, source, ETag, providers count.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from .catalog_resolver import (
    CatalogResolver,
    ResolverConfig,
)


def _format_age(seconds: float | None) -> str:
    if seconds is None:
        return "n/a"
    if seconds < 90:
        return f"{int(seconds)}s"
    if seconds < 5400:
        return f"{int(seconds / 60)}m"
    if seconds < 86400 * 2:
        return f"{seconds / 3600:.1f}h"
    return f"{seconds / 86400:.1f}d"


def _diff_providers(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[str]]:
    before_keys = set(before.keys())
    after_keys = set(after.keys())
    added = sorted(after_keys - before_keys)
    removed = sorted(before_keys - after_keys)
    changed = sorted(k for k in before_keys & after_keys if before[k] != after[k])
    return {"added": added, "removed": removed, "changed": changed}


def cmd_update(args: argparse.Namespace) -> int:
    config = ResolverConfig.from_env()
    resolver = CatalogResolver(config=config)
    status_before = resolver.status()

    # Capture current cache for diff
    before_payload: dict[str, Any] = {}
    for tier in ("private", "public"):
        cached = resolver._cache.load(tier)  # noqa: SLF001 — intentional
        if cached is not None:
            before_payload = cached.payload
            break

    if args.check:
        # Don't fetch — just inspect TTL
        for tier in ("private", "public"):
            entry = status_before["tiers"].get(tier, {})
            if entry.get("present") and entry.get("age_seconds", 1e9) < config.refresh_interval_seconds:
                print(f"fresh ({tier}, age {_format_age(entry['age_seconds'])})")
                return 0
        print("stale or missing")
        return 1

    resolved = resolver.resolve(force_refresh=True)
    if resolved.source == "empty":
        print(f"ERROR: no catalog source available; notes={resolved.notes}", file=sys.stderr)
        return 2

    after_providers = resolved.payload.get("providers", {})
    print(f"updated: source={resolved.source} providers={len(after_providers)}")
    if resolved.etag:
        print(f"  etag: {resolved.etag}")

    if args.diff:
        before_providers = before_payload.get("providers", {}) if before_payload else {}
        diff = _diff_providers(before_providers, after_providers)
        if any(diff.values()):
            for label in ("added", "removed", "changed"):
                if diff[label]:
                    print(f"  {label}:")
                    for entry in diff[label]:
                        print(f"    - {entry}")
        else:
            print("  no provider-level changes")

    return 0


def cmd_status(args: argparse.Namespace) -> int:
    resolver = CatalogResolver()
    status = resolver.status()

    if args.json:
        print(json.dumps(status, indent=2, default=str))
        return 0

    print("Catalog cache status")
    print("-" * 40)
    for tier in ("private", "public"):
        entry = status["tiers"][tier]
        if not entry.get("present"):
            print(f"  {tier:8}  not cached")
            continue
        age = _format_age(entry.get("age_seconds"))
        etag = entry.get("etag") or "<none>"
        count = entry.get("providers_count", 0)
        print(f"  {tier:8}  age={age}  providers={count}  etag={etag}")

    bundled = "yes" if status.get("bundled_present") else "no"
    print(f"  bundled  present={bundled}", end="")
    if status.get("bundled_present"):
        print(f"  providers={status.get('bundled_providers_count', 0)}")
    else:
        print()
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="faigate-models",
        description="Manage the faigate provider catalog cache.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_update = sub.add_parser("update", help="Refresh the cached catalog from remote.")
    p_update.add_argument(
        "--check",
        action="store_true",
        help="Exit 0 if cache is fresh, 1 if stale, 2 on error. No network.",
    )
    p_update.add_argument(
        "--diff",
        action="store_true",
        help="Show provider deltas after refresh.",
    )
    p_update.set_defaults(func=cmd_update)

    p_status = sub.add_parser("status", help="Show cache state.")
    p_status.add_argument("--json", action="store_true", help="Emit JSON.")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
