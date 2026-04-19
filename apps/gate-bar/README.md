# fusionAIze Gate Bar

A macOS menubar companion for the [faigate](../../README.md) local gateway.
Shows every active provider's quota at a glance, colour-coded by severity,
so you can answer "am I about to hit a session cap?" in under three seconds
without switching tabs.

> **Status:** v0.1 — scaffold in place, read-only consumer of the local
> gateway's `/api/quotas` endpoint. Sparkle auto-update, notifications,
> code signing, and Homebrew cask distribution are tracked separately and
> not wired up yet.

## What it does today

- **Menubar label** — `fAI · 83%` plus a coloured dot for the tightest
  window across all active brands. Click to open the popover.
- **Popover** — one card per brand (Claude, Codex, DeepSeek, …), sorted
  worst-alert first. Each card shows package bars with a pace marker,
  identity line, and reset time.
- **"Available to add" mini-catalog** — brands the operator hasn't wired
  up yet, each with a deep link to the Operator Cockpit's onboarding flow.
- **Preferences** — gateway URL, Cockpit URL, refresh cadence (manual /
  1 / 2 / 5 / 15 min; default 5).
- **Privacy posture** — reads from `127.0.0.1` only. Gate Bar never talks
  to a fusionAIze-hosted service; the "Cockpit ↗" button just opens a web
  page in your default browser.

## Design anchors

The full design doc is at `../../docs/GATE-BAR-DESIGN.md`. Three rules
shape every file in this directory:

1. **Pure HTTP client.** No shared state, no socket, no filesystem
   coupling with the Python daemon. Every provider the Gate Bar renders
   is discovered at runtime from `GET /api/quotas`.
2. **macOS 14+ Sonoma.** Two-year-old Intel MacBooks still run it.
   SwiftUI surface is the Sonoma subset: `ObservableObject` + Combine,
   plain `Color`, no `@Observable`, no `MeshGradient`.
3. **Read-only.** Nothing in the menubar writes config or wakes up an
   onboarding wizard. Every action that mutates state deep-links to the
   Operator Cockpit.

## Build & run

Requires the Xcode Command Line Tools (`xcode-select --install`) or
Xcode.app. Swift 5.9+ toolchain.

```bash
cd apps/gate-bar
swift build                  # debug build of the executable target
swift run GateBar            # launches the menubar app
```

The app launches as a `LSUIElement`-style menubar-only process — there's
no Dock icon or main window. Quit from the popover's "Quit" button or via
`⌘Q` while Gate Bar is the frontmost app.

### Running against a local gateway

By default Gate Bar talks to `http://127.0.0.1:4001` — the faigate
default. If you run the gateway on a different port, update it under
`Preferences → Gateway`.

### Tests

```bash
./scripts/swift-test.sh
```

We use the **Swift Testing** framework (`import Testing`) rather than
XCTest because the Command Line Tools ship Testing but not XCTest. The
wrapper script adds the framework search paths dyld needs at runtime; on
a machine with Xcode.app, plain `swift test` also works.

Current coverage (13 tests, 3 suites):

- JSON-decode round-trip against a canned `/api/quotas` payload.
- Forward compatibility — unknown JSON fields don't break decode.
- `AlertLevel` classification (server-label precedence, ratio fallback,
  unknown-string degradation, severity ordering).
- `QuotaStore` transforms (brand grouping, worst-alert sort, tie-break
  rules, tightest-window menubar summary, identity propagation).

## File map

```
Package.swift               # SPM manifest, .macOS(.v14), executable target
Sources/GateBar/
  GateBarApp.swift          # @main, MenuBarExtra + Settings scenes
  Models.swift              # Codable mirrors of /api/quotas (plus BrandGroup, AlertLevel)
  QuotaClient.swift         # URLSession-backed actor, the only network I/O
  QuotaStore.swift          # ObservableObject — grouping, sorting, menubar summary, timer
  Preferences.swift         # UserDefaults-backed @Published wrapper
  Theme.swift               # Colour palette mirroring the web widget's CSS variables
  PopoverView.swift         # The popover shell — active cards + catalog + footer
  BrandCardView.swift       # Per-brand card + per-package row with pace tick
  PreferencesView.swift     # Settings window — 4 controls, no wizards
Tests/GateBarTests/
  ModelsTests.swift         # JSON decode + AlertLevel classification
  QuotaStoreTests.swift     # Grouping / sorting / menubar-summary
scripts/
  swift-test.sh             # `swift test` with CLT-compatible rpaths
```

## Roadmap (not yet shipped)

- [ ] Sparkle 2 auto-update (EdDSA-signed appcast, notarized .dmg from
      GitHub releases).
- [ ] Notifications — threshold alerts (session 80 %, weekly 80 %,
      pace +10 %) via `UserNotifications`.
- [ ] Launch at login via `SMAppService.mainApp.register()`.
- [ ] `.app` bundle + notarization pipeline in `/.github/workflows`.
- [ ] Homebrew cask: `brew install --cask fusionaize/tap/gate-bar`.
- [ ] Hide-menubar-icon toggle (keeps the app running but invisible).

These are release-engineering passes, not app-code. Tracked against the
v2.3.x release milestone.
