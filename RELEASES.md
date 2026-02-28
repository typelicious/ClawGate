# Releases

This repo does not require a heavy release process. Use lightweight tags plus GitHub Releases.

## Release Flow

1. Make sure `main` is green.
2. Update [CHANGELOG.md](./CHANGELOG.md):
   - Move the relevant notes from `Unreleased` into a versioned section.
   - Keep the notes focused on user-visible changes.
3. Create an annotated tag from `main`.
4. Push the tag to GitHub.
5. Create a GitHub Release from that tag.
6. Use the changelog entry as the release notes, then add any short upgrade notes if needed.

## Example

```bash
git checkout main
git pull --ff-only origin main
git tag -a v0.1.0 -m "ClawGate v0.1.0"
git push origin v0.1.0
```

Then open GitHub Releases and publish a release for `v0.1.0`.

## Versioning Guidance

- Prefer simple, semantic-ish version tags such as `v0.1.0`, `v0.2.0`, `v0.2.1`.
- Use a minor bump for new features and notable operational changes.
- Use a patch bump for fixes and documentation-only polish that affects users or operators.
- Avoid promising strict semantic versioning unless the project decides to enforce it consistently.

## What Belongs In Release Notes

- New providers or routing behavior changes
- API surface changes
- Deployment or operational changes
- Breaking changes or migration notes
- Fixes that affect request behavior, fallbacks, or observability
