#!/usr/bin/env python3
"""Strip non-faigate content from changelog / release notes.

The prerelease workflow runs this against `git-cliff` output to drop
bullets that mention personal tooling or local setup details before the
notes hit the public GitHub release. Patterns are intentionally narrow:
when in doubt the line is kept and the human reviewer catches it.

Usage:
    filter-changelog.py <input.md>           # writes filtered notes to stdout
    filter-changelog.py --check <input.md>   # exit 1 if anything would be dropped
    filter-changelog.py --self-test          # run the embedded test cases
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Each pattern is a regex (case-insensitive). Add only when the term has
# zero legitimate place in faigate-facing release notes.
DENY_PATTERNS: list[str] = [
    r"\bICM\b",
    r"mempalace",
    r"envctl",
    r"\bRTK\b",
    r"OpenCode",
    r"CodeNomad",
    r"Codex(?:\s+CLI)?",
    r"Claude Code",
    r"~/Library/",
    r"~/Documents/",
    r"~/\.mempalace",
    r"/Users/[A-Za-z][\w.-]+",
]

_DENY_RE = re.compile("|".join(DENY_PATTERNS), re.IGNORECASE)
_BULLET_RE = re.compile(r"^\s*[-*]\s+")
_HEADING_RE = re.compile(r"^\s*#{1,6}\s+")


def filter_text(text: str) -> tuple[str, list[str]]:
    """Return ``(filtered_text, dropped_lines)``.

    Drops bullet lines whose content matches any deny pattern. Then drops
    headings that lose all their bullets. Collapses runs of blank lines.
    Non-bullet lines are never filtered — they're prose the human wrote.
    """
    lines = text.splitlines()
    dropped: list[str] = []
    kept: list[str] = []

    for line in lines:
        if _BULLET_RE.match(line) and _DENY_RE.search(line):
            dropped.append(line)
            continue
        kept.append(line)

    # Drop now-empty headings (no bullets remain in their section).
    pruned: list[str] = []
    i = 0
    while i < len(kept):
        line = kept[i]
        if _HEADING_RE.match(line):
            j = i + 1
            section_has_content = False
            while j < len(kept) and not _HEADING_RE.match(kept[j]):
                if kept[j].strip():
                    section_has_content = True
                    break
                j += 1
            if not section_has_content:
                i += 1
                continue
        pruned.append(line)
        i += 1

    result = "\n".join(pruned)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.rstrip() + "\n", dropped


# ── self test ──────────────────────────────────────────────────────────


_SELF_TEST_INPUT = """\
## v2.4.0 - 2026-04-26

### Added
- feat(catalog): runtime sync engine
- chore: configured envctl cluster `faigate` with metadata vars
- ICM data archived for migration to mempalace
- Wired into Claude Code via /Users/andrelange/.claude.json

### Fixed
- fix: trailing newline on bundled snapshot

### Internal
- chore: misc cleanups in ~/Library/Caches
"""

_SELF_TEST_EXPECTED_DROPS = 4
_SELF_TEST_MUST_KEEP = [
    "feat(catalog): runtime sync engine",
    "fix: trailing newline on bundled snapshot",
]


def _self_test() -> int:
    out, dropped = filter_text(_SELF_TEST_INPUT)
    failed = False
    if len(dropped) != _SELF_TEST_EXPECTED_DROPS:
        print(
            f"FAIL: expected {_SELF_TEST_EXPECTED_DROPS} drops, got {len(dropped)}",
            file=sys.stderr,
        )
        for line in dropped:
            print(f"  dropped: {line}", file=sys.stderr)
        failed = True
    for keeper in _SELF_TEST_MUST_KEEP:
        if keeper not in out:
            print(f"FAIL: should have kept '{keeper}'", file=sys.stderr)
            failed = True
    if "Internal" in out:
        print("FAIL: empty 'Internal' section should have been pruned", file=sys.stderr)
        failed = True
    if failed:
        print("---OUTPUT---", file=sys.stderr)
        print(out, file=sys.stderr)
        return 1
    print("ok: self-test passed")
    return 0


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "--self-test":
        return _self_test()
    if len(argv) == 3 and argv[1] == "--check":
        text = Path(argv[2]).read_text(encoding="utf-8")
        _, dropped = filter_text(text)
        if dropped:
            print(f"would drop {len(dropped)} line(s):", file=sys.stderr)
            for line in dropped:
                print(f"  {line}", file=sys.stderr)
            return 1
        return 0
    if len(argv) == 2:
        text = Path(argv[1]).read_text(encoding="utf-8")
        out, dropped = filter_text(text)
        sys.stdout.write(out)
        if dropped:
            print(f"# filtered {len(dropped)} non-faigate line(s)", file=sys.stderr)
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
