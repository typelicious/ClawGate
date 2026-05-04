#!/usr/bin/env python3
"""
quota-helper — provider quota fetcher prototype.

Fetches real usage data directly from provider web APIs, mirroring
how CodexBar works: browser cookies for web-auth providers, API keys
or OAuth tokens for programmatic providers.

Providers implemented:
  - claude      : Chrome sessionKey cookie → claude.ai/api/organizations/{org}/usage
  - openrouter  : OPENROUTER_API_KEY env var → openrouter.ai/api/v1/credits
  - gemini      : gcloud OAuth token → cloudcode-pa.googleapis.com (WIP)
  - cursor      : Chrome session cookies → cursor.sh/api/usage-summary (WIP)

Output is a list of ProviderSnapshot dicts:
  {
    "provider": "claude",
    "brand":    "Claude",
    "windows": [
      {"label": "Session", "used_pct": 13.0, "resets_at": "2026-04-20T07:00:00Z"},
      {"label": "Weekly",  "used_pct": 94.0, "resets_at": "2026-04-23T20:00:00Z"},
    ],
    "credits": {"used": 17.26, "limit": 17.0, "currency": "EUR"},  # optional
    "error": null,
  }
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# Chrome cookie decryption (macOS v10 format)
# ---------------------------------------------------------------------------


def _chrome_key() -> bytes:
    pw = subprocess.check_output(["security", "find-generic-password", "-s", "Chrome Safe Storage", "-w"]).strip()
    return hashlib.pbkdf2_hmac("sha1", pw, b"saltysalt", 1003, dklen=16)


def _decrypt_chrome_cookie(enc: bytes, key: bytes) -> str:
    """AES-128-CBC, fixed IV=space*16, v10 prefix, PKCS7 padding.

    Chrome on macOS stores a binary prefix ending with 0x60 before the
    actual ASCII value. We split on the last 0x60 byte.
    """
    try:
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    except ImportError:
        raise RuntimeError("pip install cryptography")

    if enc[:3] != b"v10":
        return enc.decode("utf-8", errors="ignore")
    payload = enc[3:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(b" " * 16), backend=default_backend())
    dec = cipher.decryptor().update(payload)
    pad = dec[-1]
    raw = dec[:-pad]
    idx = raw.rfind(b"\x60")
    return raw[idx + 1 :].decode("ascii", errors="ignore") if idx >= 0 else raw.decode("ascii", errors="ignore")


def _chrome_cookies(domain: str, names: list[str]) -> dict[str, str]:
    db = os.path.expanduser("~/Library/Application Support/Google/Chrome/Default/Cookies")
    if not os.path.exists(db):
        return {}
    tmp = tempfile.mktemp(suffix=".sqlite")
    shutil.copy2(db, tmp)
    try:
        conn = sqlite3.connect(tmp)
        like = f"%{domain}%"
        placeholders = ",".join("?" * len(names))
        rows = conn.execute(
            f"SELECT name, encrypted_value FROM cookies WHERE host_key LIKE ? AND name IN ({placeholders})",
            [like, *names],
        ).fetchall()
        conn.close()
    finally:
        os.unlink(tmp)

    key = _chrome_key()
    return {name: _decrypt_chrome_cookie(enc, key) for name, enc in rows}


# ---------------------------------------------------------------------------
# HTTP helper
# ---------------------------------------------------------------------------


def _get(url: str, headers: dict[str, str], timeout: int = 8) -> Any:
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _post(url: str, body: Any, headers: dict[str, str], timeout: int = 8) -> Any:
    data = json.dumps(body).encode()
    headers = {**headers, "Content-Type": "application/json"}
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


# ---------------------------------------------------------------------------
# Provider: Claude (web cookies)
# ---------------------------------------------------------------------------


def fetch_claude() -> dict:
    result: dict = {"provider": "claude", "brand": "Claude", "windows": [], "credits": None, "error": None}
    try:
        cookies = _chrome_cookies("claude.ai", ["sessionKey", "lastActiveOrg"])
        session = cookies.get("sessionKey", "")
        org = cookies.get("lastActiveOrg", "")
        if not session or not org:
            result["error"] = "No claude.ai session cookie found in Chrome"
            return result

        hdrs = {
            "Cookie": f"sessionKey={session}; lastActiveOrg={org}",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
            "Referer": "https://claude.ai/settings/usage",
        }
        data = _get(f"https://claude.ai/api/organizations/{org}/usage", hdrs)

        def window(label: str, key: str) -> dict | None:
            w = data.get(key)
            if not w:
                return None
            return {
                "label": label,
                "used_pct": w.get("utilization", 0.0),
                "resets_at": w.get("resets_at"),
            }

        for w in [
            window("Session (5h)", "five_hour"),
            window("Weekly", "seven_day"),
            window("Weekly Opus", "seven_day_opus"),
            window("Weekly Sonnet", "seven_day_sonnet"),
            window("Weekly Design", "seven_day_omelette"),
        ]:
            if w:
                result["windows"].append(w)

        extra = data.get("extra_usage")
        if extra:
            result["credits"] = {
                "used": extra.get("used_credits", 0) / 100,
                "limit": extra.get("monthly_limit", 0) / 100,
                "used_pct": extra.get("utilization", 0.0),
                "currency": extra.get("currency", "USD"),
            }
    except Exception as exc:
        result["error"] = str(exc)
    return result


# ---------------------------------------------------------------------------
# Provider: OpenRouter (API key)
# ---------------------------------------------------------------------------


def fetch_openrouter(api_key: str | None = None) -> dict:
    result: dict = {"provider": "openrouter", "brand": "OpenRouter", "windows": [], "credits": None, "error": None}
    key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        result["error"] = "OPENROUTER_API_KEY not set"
        return result
    try:
        hdrs = {"Authorization": f"Bearer {key}", "Accept": "application/json"}
        data = _get("https://openrouter.ai/api/v1/credits", hdrs)
        usage = data.get("data", data)
        total = usage.get("total_credits", 0)
        used = usage.get("total_usage", 0)
        if total > 0:
            # Pre-paid credits: show % consumed
            result["credits"] = {
                "used": round(used, 4),
                "total": round(total, 4),
                "used_pct": round(used / total * 100, 1),
                "currency": "USD",
                "mode": "prepaid",
            }
        else:
            # Pay-as-you-go: no budget cap, just show spend
            result["credits"] = {
                "used": round(used, 4),
                "total": None,
                "used_pct": None,
                "currency": "USD",
                "mode": "payg",
            }
    except Exception as exc:
        result["error"] = str(exc)
    return result


# ---------------------------------------------------------------------------
# faigate token store (~/.config/faigate/tokens.json)
# ---------------------------------------------------------------------------


def _faigate_token(provider_key: str) -> str | None:
    """Return a non-expired access_token from faigate's token store, or None."""
    path = os.path.expanduser("~/.config/faigate/tokens.json")
    if not os.path.exists(path):
        return None
    try:
        data = json.loads(open(path).read())
        entry = data.get(provider_key, {})
        token = entry.get("access_token")
        expiry = entry.get("expiry_date") or entry.get("expires_at")
        if not token:
            return None
        if expiry:
            # expiry_date may be epoch-ms or ISO string
            if isinstance(expiry, int | float):
                ts = expiry / 1000 if expiry > 1e10 else expiry
                if ts < datetime.now(timezone.utc).timestamp():
                    return None  # expired
            elif isinstance(expiry, str):
                try:
                    dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                    if dt < datetime.now(timezone.utc):
                        return None
                except Exception:
                    pass
        return token
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Provider: Gemini / Google Cloud Code (OAuth token via faigate or gcloud)
# ---------------------------------------------------------------------------


def fetch_gemini() -> dict:
    result: dict = {"provider": "gemini", "brand": "Gemini", "windows": [], "credits": None, "error": None}
    try:
        # Prefer faigate's stored token; fall back to gcloud CLI
        token = _faigate_token("gemini-cli")
        if not token:
            try:
                token = (
                    subprocess.check_output(["gcloud", "auth", "print-access-token"], stderr=subprocess.DEVNULL)
                    .strip()
                    .decode()
                )
            except (FileNotFoundError, subprocess.CalledProcessError):
                result["error"] = "No valid Gemini token (faigate expired, gcloud not available)"
                return result

        hdrs = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
        data = _post(
            "https://cloudcode-pa.googleapis.com/v1internal:retrieveUserQuota",
            {},
            hdrs,
        )
        for quota in data.get("quotas", []):
            frac = quota.get("remainingFraction", 1.0)
            used_pct = round((1.0 - frac) * 100, 1)
            label = quota.get("tokenType", quota.get("modelId", "Unknown"))
            resets_at = quota.get("resetTime")
            result["windows"].append({"label": label, "used_pct": used_pct, "resets_at": resets_at})
        if not result["windows"]:
            result["error"] = "No quota data in response"
    except urllib.error.HTTPError as exc:
        result["error"] = f"HTTP {exc.code}"
    except Exception as exc:
        result["error"] = str(exc)
    return result


# ---------------------------------------------------------------------------
# Provider: Cursor (web cookies)
# ---------------------------------------------------------------------------


def fetch_cursor() -> dict:
    result: dict = {"provider": "cursor", "brand": "Cursor", "windows": [], "credits": None, "error": None}
    try:
        cookie_names = [
            "WorkosCursorSessionToken",
            "__Secure-next-auth.session-token",
            "next-auth.session-token",
        ]
        cookies = _chrome_cookies("cursor.sh", cookie_names)
        # Also check cursor.com
        if not any(cookies.values()):
            cookies = _chrome_cookies("cursor.com", cookie_names)

        session = next((v for v in cookies.values() if v), "")
        if not session:
            result["error"] = "No Cursor session cookie in Chrome"
            return result

        cookie_str = "; ".join(f"{k}={v}" for k, v in cookies.items() if v)
        hdrs = {
            "Cookie": cookie_str,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Accept": "application/json",
        }
        data = _get("https://www.cursor.com/api/usage-summary", hdrs)
        # Cursor returns percentages for Auto, Composer, API
        for key, label in [("auto", "Auto"), ("composer", "Composer"), ("api", "API")]:
            w = data.get(key, {})
            if w:
                used_pct = w.get("usedPercent", w.get("used_pct", 0.0))
                result["windows"].append(
                    {
                        "label": label,
                        "used_pct": used_pct,
                        "resets_at": data.get("billingPeriodEnd") or data.get("nextReset"),
                    }
                )
    except Exception as exc:
        result["error"] = str(exc)
    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

FETCHERS = {
    "claude": fetch_claude,
    "openrouter": fetch_openrouter,
    "gemini": fetch_gemini,
    "cursor": fetch_cursor,
}


def _fmt_pct(p: float) -> str:
    return f"{p:.1f}%"


def _fmt_reset(iso: str | None) -> str:
    if not iso:
        return ""
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        delta = dt - datetime.now(timezone.utc)
        h, rem = divmod(int(delta.total_seconds()), 3600)
        m = rem // 60
        if h > 48:
            return f"in {h // 24}d"
        if h > 0:
            return f"in {h}h {m}m"
        return f"in {m}m"
    except Exception:
        return iso[:10]


def print_report(snapshots: list[dict]) -> None:
    for snap in snapshots:
        brand = snap["brand"]
        err = snap.get("error")
        print(f"\n{'─' * 48}")
        print(f"  {brand}")
        if err:
            print(f"  ✗ {err}")
            continue
        for w in snap.get("windows", []):
            pct = _fmt_pct(w["used_pct"])
            rst = _fmt_reset(w.get("resets_at"))
            bar_w = 30
            filled = int(w["used_pct"] / 100 * bar_w)
            bar = "█" * filled + "░" * (bar_w - filled)
            print(f"  {w['label']:<18} {pct:>6}  {bar}  {rst}")
        credits = snap.get("credits")
        if credits:
            cur = credits.get("currency", "USD")
            used = credits.get("used", 0)
            total = credits.get("total")
            used_pct = credits.get("used_pct")
            if credits.get("mode") == "payg" or total is None:
                print(f"  {'Spend (PAYG)':<18} {'':>6}  ${used:.4f} {cur}")
            else:
                bar_w = 30
                filled = int((used_pct or 0) / 100 * bar_w)
                bar = "█" * filled + "░" * (bar_w - filled)
                print(f"  {'Credits':<18} {_fmt_pct(used_pct or 0):>6}  {bar}  {used:.2f}/{total:.2f} {cur}")


def _load_faigate_env() -> None:
    """Load /opt/homebrew/etc/faigate/.env into os.environ (no-op if missing)."""
    env_path = "/opt/homebrew/etc/faigate/.env"
    if not os.path.exists(env_path):
        return
    for line in open(env_path):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = val


if __name__ == "__main__":
    _load_faigate_env()

    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    json_only = "--json-only" in flags  # machine-readable mode: JSON to stdout only

    requested = args or list(FETCHERS.keys())
    snapshots = []
    for name in requested:
        if name not in FETCHERS:
            print(f"Unknown provider: {name}. Available: {', '.join(FETCHERS)}", file=sys.stderr)
            continue
        print(f"Fetching {name}...", end=" ", flush=True, file=sys.stderr if json_only else sys.stdout)
        snap = FETCHERS[name]()
        status = "ok" if not snap.get("error") else f"error: {snap['error']}"
        print(status, file=sys.stderr if json_only else sys.stdout)
        snapshots.append(snap)

    if json_only:
        print(json.dumps(snapshots))
    else:
        print_report(snapshots)
        print(f"\n{'─' * 48}")
        if "--json" in flags:
            print(json.dumps(snapshots, indent=2))
