# faigate-model-updater — Patterns & Guidelines

## Architecture Patterns

- **Two-layer catalog model**: `ProviderCatalogRefresher` (existing) handles
  vendor doc scraping for model discovery. `MetadataCatalogSync` (new) syncs
  the curated catalog from the metadata repo. They feed the same loader and
  must not be conflated.
- **Resolution chain pattern**: private → public → bundled. Each tier returns
  `(payload, source)`; downstream code never assumes which tier won.
- **Atomic swap-in**: cache writes go to `*.tmp` + rename. Schema validation
  happens before swap. Old cache stays usable on validation failure.
- **Two-clock cache**: ETag for change detection, TTL for freshness ceiling.

## Code Standards

- All HTTP uses `httpx` (already a dep). No new HTTP client deps.
- Schema validation via `jsonschema` (already a dep).
- New module: `faigate/metadata_catalog_sync.py` (Sync), `faigate/catalog_cache.py` (Cache),
  `faigate/catalog_resolver.py` (Resolver).
- All public functions have type hints. Pydantic for `FetchResult`,
  `ResolvedCatalog`, `SyncError`.
- Logging via stdlib `logging` (gateway logger). NEVER log full headers or
  the token. Use `_redact()` helper.

## Gotchas & Solutions

- **GitHub Raw cache stickiness**: jsdelivr-style mirrors cache aggressively
  (10min). Use raw.githubusercontent.com for low-latency reads, mirror for
  resilience.
- **PAT scopes**: fine-grained PAT requires explicit org allowlist. Document
  this clearly in CATALOG-AUTH.md.
- **fcntl on Windows**: use `portalocker` lib or skip lock on Windows (single
  refresher only — fall back to atomic rename).
- **Rate limit math**: 60 req/h anonymous, 5000/h auth. With 24h TTL +
  ETag (304 doesn't count), we're 100x under both limits.

## Integration Notes

- `provider_catalog.py:_resolve_catalog_path()` is the integration point.
  Insert resolver between explicit env override and bundled fallback.
- `build_catalog_alerts` already has alert types — extend rather than add new
  alert system.
- Daemon hook: `quota_poller.py` shows the pattern for periodic background
  work.

## Testing Notes

- Use `respx` for HTTP mocks. Pattern already established in faigate test
  suite (check tests/ for examples).
- Snapshot tests for catalog content go in `tests/catalog/` against fixtures.
- Always test the secret-not-logged invariant explicitly.
