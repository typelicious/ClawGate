import Testing
import Foundation
@testable import GateBar

// Uses the Swift Testing framework (`swift test` picks it up automatically
// on Sonoma+). XCTest is intentionally avoided because it only ships with
// a full Xcode install — the Swift Testing framework is bundled with the
// Command Line Tools too, so CI and fresh dev machines get green tests
// without needing Xcode.app.

// MARK: - JSON decoding

private let sample = """
{
  "packages": [
    {
      "package_id": "anthropic-pro-5h-session",
      "package_name": "Pro · 5-h session",
      "provider_id": "anthropic-claude",
      "provider_group": "anthropic",
      "brand": "Claude",
      "brand_slug": "claude",
      "package_type": "rolling_window",
      "used_ratio": 0.83,
      "elapsed_ratio": 0.62,
      "pace_delta": 0.21,
      "alert": "topup",
      "reset_at": "2026-04-19T22:00:00Z",
      "used_display": "83 / 100",
      "total_display": "100",
      "identity": {"login_method": "OAuth", "credential": "claude-code"}
    },
    {
      "package_id": "deepseek-pay-as-you-go",
      "package_name": "Pay-as-you-go",
      "provider_id": "deepseek-chat",
      "provider_group": "deepseek",
      "brand": "DeepSeek",
      "brand_slug": "deepseek",
      "package_type": "credits",
      "used_ratio": 0.0,
      "elapsed_ratio": null,
      "pace_delta": null,
      "alert": "ok",
      "projected_days_left": 42,
      "used_display": "$0.00",
      "total_display": "$28.42",
      "identity": {"login_method": "API key", "credential": "DEEPSEEK_API_KEY"}
    }
  ],
  "by_alert": {"topup": 1, "ok": 1},
  "catalog_suggestions": [
    {"brand": "Cursor", "brand_slug": "cursor", "tagline": "Pro · $20/mo · 500 fast req/mo"}
  ],
  "skipped_packages": [
    {"package_id": "qwen-free-daily", "brand": "Qwen", "brand_slug": "qwen", "requires": "qwen-portal"}
  ]
}
""".data(using: .utf8)!

@Suite("QuotaResponse JSON decode")
struct QuotaResponseDecodeTests {
    @Test func decodesFullResponse() throws {
        let resp = try JSONDecoder().decode(QuotaResponse.self, from: sample)
        #expect(resp.packages.count == 2)
        #expect(resp.catalogSuggestions?.count == 1)
        #expect(resp.skippedPackages?.count == 1)

        let claude = resp.packages[0]
        #expect(claude.brand == "Claude")
        #expect(claude.brandSlug == "claude")
        #expect(abs((claude.paceDelta ?? 0) - 0.21) < 1e-9)
        #expect(claude.identity?.loginMethod == "OAuth")
        #expect(claude.packageName == "Pro · 5-h session")
    }

    @Test func creditsPackageSurfacesNilPace() throws {
        let resp = try JSONDecoder().decode(QuotaResponse.self, from: sample)
        let ds = resp.packages[1]
        #expect(ds.paceDelta == nil)
        #expect(ds.elapsedRatio == nil)
        #expect(ds.projectedDaysLeft == 42)
    }

    @Test func unknownFieldsAreIgnored() throws {
        // The Python side adds fields every few releases. Gate Bar must
        // decode forward-compatible responses without failing so we can
        // evolve the contract in one direction at a time.
        let jsonWithExtras = """
        {
          "packages": [{
            "package_id": "x",
            "brand": "X",
            "brand_slug": "x",
            "used_ratio": 0.1,
            "alert": "ok",
            "invented_field_nobody_asked_for": 42
          }],
          "header_snapshots": {"x": {"dialect": "openai"}},
          "has_exhausted": false
        }
        """.data(using: .utf8)!
        _ = try JSONDecoder().decode(QuotaResponse.self, from: jsonWithExtras)
    }
}

// MARK: - AlertLevel

@Suite("AlertLevel classification")
struct AlertLevelTests {
    @Test func serverAlertWinsOverRatio() {
        #expect(AlertLevel(rawAlert: "exhausted", usedRatio: 0.01) == .exhausted)
    }

    @Test func fallsBackToRatioThresholds() {
        #expect(AlertLevel(rawAlert: nil, usedRatio: 0.0) == .ok)
        #expect(AlertLevel(rawAlert: nil, usedRatio: 0.55) == .watch)
        #expect(AlertLevel(rawAlert: nil, usedRatio: 0.75) == .topup)
        #expect(AlertLevel(rawAlert: nil, usedRatio: 0.95) == .urgent)
        #expect(AlertLevel(rawAlert: nil, usedRatio: 1.2) == .exhausted)
    }

    @Test func unknownAlertStringFallsBackToRatio() {
        // Defensive: the server might ship a new level before Gate Bar
        // knows about it (e.g. "frozen"). Degrade to the ratio fallback,
        // don't crash.
        #expect(AlertLevel(rawAlert: "frozen", usedRatio: 0.72) == .topup)
    }

    @Test func severityOrdering() {
        #expect(AlertLevel.urgent > .topup)
        #expect(AlertLevel.exhausted > .urgent)
        #expect(!(AlertLevel.ok > .watch))
    }
}
