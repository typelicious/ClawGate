# PRD — faigate Model & Catalog Updater

**Project:** faigate-model-updater
**Created:** 2026-04-26
**Owner:** André Lange (typelicious@gmail.com)
**Status:** Draft (medium mode)

## 1. Executive Summary

faigate ships with a bundled provider catalog (`fusionaize-metadata`) that goes
stale every time a vendor releases a new model or pricing tier. Today the
catalog is loaded from a local checkout via `FAIGATE_PROVIDER_METADATA_DIR`,
which means installed users never get pricing/model updates without a faigate
release.

This PRD introduces a **runtime catalog sync** that pulls a curated catalog
from a remote (GitHub Raw) without requiring a faigate version bump. It also
splits metadata into a **public** repo (raw pricing + schemas) and the existing
**private** repo (overlays, routing heuristics, evaluations).

## 2. Problem Statement

- New models (`claude-opus-4-7`, `claude-haiku-4-5`, `gpt-5.5` reasoning tiers,
  `deepseek-v4`) and expiring tracks (Kilo GLM-5 free → 2026-04-26) require
  catalog edits today.
- Installed faigate instances are pinned to the catalog at build time.
- The single private metadata repo can't be consumed by anonymous installs
  without a token, and we want pricing data to "just work" for OSS users.
- IP exposure: routing heuristics, evaluations and negative-lists must not
  leak.

## 3. Target Users

- **OSS faigate users** — anonymous, want pricing/model freshness, no GitHub
  account required.
- **Pro/internal users** — authenticated via PAT, get private overlays
  (routing, scoring).
- **Catalog maintainer (André)** — needs an editing flow that auto-distributes
  changes within 24h.

## 4. Solution Overview

```
faigate (installed wheel)
  ├── default_catalog.json         ← bundled fallback
  ├── MetadataCatalogSync (NEW)    ← pulls remote catalog with ETag
  │     1. Try private remote (if FAIGATE_METADATA_TOKEN set)
  │     2. Try public remote
  │     3. Bundled default
  ├── provider_catalog.py loader   ← wire sync output into existing loader
  ├── Daemon tick (24h)            ← background refresh
  └── `faigate models update` CLI  ← force / --check / --diff

fusionaize-metadata-public (NEW, public)
  └── providers/catalog.v1.json  +  schemas/

fusionaize-metadata (existing, private)
  └── products/gate/overlays.v1.json
```

This is a **distinct layer from** the existing `ProviderCatalogRefresher`
which scrapes vendor doc pages for model discovery — the new
`MetadataCatalogSync` syncs the curated catalog. They feed into the same
loader.

## 5. Functional Requirements

### 5.1 Core

- F-1 `MetadataCatalogSync` fetches `catalog.v1.json` over HTTPS with
  conditional GET (`If-None-Match` / ETag).
- F-2 Cache stored at `~/.cache/faigate/metadata/{public,private}/catalog.v1.json`
  + sibling `.etag` file.
- F-3 Resolution chain: private (if token) → public → bundled. Each falls back
  on 4xx/5xx/network error.
- F-4 24h TTL; daemon tick re-checks; manual override via
  `faigate models update [--check] [--diff]`.
- F-5 Schema validation against `schemas/provider-catalog.v1.schema.json`
  before swap-in. Invalid remote → keep current cache, raise alert.
- F-6 Alerts surfaced through existing `build_catalog_alerts` (severity:
  `warning` for stale > 7d, `error` for invalid).

### 5.2 Schema bump (v1 → v1.1, additive)

- `expires_at` (optional ISO date) per provider entry — drives "expired
  free-tier" handling.
- `tier_status` enum: `active|deprecated|expired|preview` — replaces the
  ad-hoc `notes` text scanning.

### 5.3 CLI

- `faigate models update` — force refresh, print diff vs cache.
- `faigate models update --check` — exit 0 if up-to-date, 1 if stale, 2 on
  error.
- `faigate models update --diff` — print changed providers/models only.
- `faigate models status` — last-fetched, ETag, source (private/public/
  bundled), cache age.

### 5.4 Catalog content (immediate adds)

- `claude-opus-4-7`, `claude-haiku-4-5` — Anthropic
- `gpt-5.5-low`, `gpt-5.5-medium`, `gpt-5.5-high` — OpenAI Codex (reasoning
  levels)
- `deepseek-v4` (chat + reasoner if separate per api-docs.deepseek.com)
- `kilocode`: `expires_at: 2026-04-26`, `tier_status: expired`
- `openrouter-fallback`: re-audit aliases + pricing

## 6. Non-Functional Requirements

- **NF-Perf** Sync overhead < 200ms when up-to-date (HEAD/ETag), < 1.5s on
  fresh body fetch.
- **NF-Sec** No secrets logged. PAT only read from env / config file
  (chmod 600). Schema validation prevents injection of unknown fields used as
  routing keys.
- **NF-Avail** Sync failure must never block faigate startup — fall through
  to bundled.
- **NF-Compat** Schema bump is additive. Old faigate versions ignore new
  fields without erroring.

## 7. Technical Architecture

- **HTTP layer** Reuse `httpx` already in `provider_catalog_refresh.py`.
- **Auth** `FAIGATE_METADATA_TOKEN` env var → fine-grained PAT, repo-scoped
  read-only. Header `Authorization: Bearer <token>` against
  `https://raw.githubusercontent.com/fusionAIze/fusionaize-metadata/...`.
- **Cache** Filesystem JSON + `.etag` text file. Lock file
  (`catalog.public.lock`) for daemon/CLI race safety.
- **Daemon tick** Hooked into existing background scheduler used by
  `quota_poller.py`.
- **Config** Three new keys in `config.yaml` under `metadata:`:
  - `public_catalog_url` (default GitHub Raw URL)
  - `private_catalog_url` (default GitHub Raw URL, gated by token)
  - `refresh_interval_hours` (default 24)

## 8. Success Metrics

- M-1 Time-from-edit-to-installed-user < 24h (was: a release cycle).
- M-2 100% of OSS users get pricing updates with zero auth setup.
- M-3 Schema validation rejects malformed remotes in 100% of cases.
- M-4 < 1% of refreshes fail without graceful fallback.
- M-5 No secrets in logs (verified by scrubber test).

## 9. Scope & Constraints

### In Scope (Phase 1)
- Public/private repo split.
- `MetadataCatalogSync` + cache + ETag.
- CLI commands.
- Schema v1.1 additive bump.
- Catalog content updates (Opus 4.7, GPT-5.5, DeepSeek v4, Kilo expiry,
  OpenRouter cleanup).

### Future (Roadmap)
- cosign/GPG signing (against MITM beyond TLS).
- Mirror to alternate CDNs (jsdelivr) for resilience.
- Auto-PR bot that watches vendor doc pages and proposes catalog patches.
- Schema v2 with model capability matrix.

### Out of Scope
- Vendor-doc scraping (already covered by `ProviderCatalogRefresher`).
- Per-user override of remote URL via dashboard UI (Phase 2).
- Compatibility layer for catalog versions older than v1.

## 10. Timeline

| Phase | Tasks | Effort |
|-------|-------|--------|
| Phase 0 — hot patches | Kilo expiry, Opus 4.7 add | 0.5d |
| Phase 1 — split repo | Public spinoff + rewrite paths | 1d |
| Phase 2 — sync engine | `MetadataCatalogSync`, cache, ETag, fallback | 2d |
| Phase 3 — CLI + daemon | Commands, scheduler, alerts | 1.5d |
| Phase 4 — schema v1.1 | `expires_at`, `tier_status`, validation | 1d |
| Phase 5 — content fill | All new model entries, OpenRouter audit | 0.5d |
| Phase 6 — docs + tests | README, CATALOG-UPDATER.md, integration tests | 1d |

**Total ~7.5 dev days.**

## 11. Risks

| Risk | Mitigation |
|------|-----------|
| GitHub Raw rate limits (60/h anon) | ETag → 304 doesn't count; cache TTL 24h |
| Token leak in logs | Scrubber test, never log headers |
| Schema break in remote | Validate before swap; alert on rejection |
| Public repo IP leak | Strict allowlist of fields exported to public |
| Private repo down → no overlays | Public catalog is full standalone catalog |

## 12. Assumptions

- GitHub remains the metadata host (vs S3/Cloudflare).
- Faigate users tolerate 24h pricing latency.
- Fine-grained PATs are acceptable for Pro users (vs OAuth flow — too heavy
  for v1).
