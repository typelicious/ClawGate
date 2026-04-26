"""Bundled provider catalog snapshot.

The `catalog.v1.json` file in this package is a snapshot of the curated
public provider catalog from
https://github.com/fusionAIze/fusionaize-metadata-public, embedded so
faigate has working catalog data immediately on first install — even
offline, before the runtime sync engine has fetched the latest copy.

The snapshot is refreshed by ``scripts/refresh-bundled-catalog`` (or
manually) at release-cut time. At runtime, ``CatalogResolver`` prefers
freshly-synced caches and falls back to this snapshot when both
remote tiers are unavailable.
"""
