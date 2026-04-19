import Testing
import Foundation
@testable import GateBar

// Pure data-transform tests for the store: grouping, sorting, menubar
// summary. HTTP + timer behaviour is deliberately out of scope — it gets
// exercised end-to-end once the app is running against a live gateway.

@Suite("QuotaStore transforms", .serialized)
@MainActor
struct QuotaStoreTests {
    private func makeStore() -> QuotaStore {
        // Fresh, transient UserDefaults so tests never leak state into the
        // developer's real preferences plist.
        let suite = UserDefaults(suiteName: "gate-bar-tests-\(UUID().uuidString)")!
        let prefs = Preferences(defaults: suite)
        return QuotaStore(preferences: prefs)
    }

    private func pkg(
        _ id: String,
        brand: String,
        slug: String,
        alert: String,
        ratio: Double,
        identity: Identity? = nil
    ) -> QuotaPackage {
        let identityFragment: String
        if let identity {
            identityFragment = ",\"identity\":{\"login_method\":\"\(identity.loginMethod)\",\"credential\":\"\(identity.credential)\"}"
        } else {
            identityFragment = ""
        }
        let json = """
        {
          "package_id": "\(id)",
          "brand": "\(brand)",
          "brand_slug": "\(slug)",
          "alert": "\(alert)",
          "used_ratio": \(ratio)\(identityFragment)
        }
        """
        return try! JSONDecoder().decode(QuotaPackage.self, from: Data(json.utf8))
    }

    @Test func groupsPackagesByBrandSlug() {
        let store = makeStore()
        store.apply(QuotaResponse(
            packages: [
                pkg("a1", brand: "Claude", slug: "claude", alert: "ok", ratio: 0.2),
                pkg("a2", brand: "Claude", slug: "claude", alert: "watch", ratio: 0.6),
                pkg("b1", brand: "DeepSeek", slug: "deepseek", alert: "ok", ratio: 0.05),
            ],
            byAlert: nil, catalogSuggestions: nil, skippedPackages: nil
        ))
        #expect(store.brands.count == 2)
        let claude = store.brands.first { $0.brandSlug == "claude" }
        #expect(claude?.packages.count == 2)
    }

    @Test func sortsWorstAlertFirst() {
        let store = makeStore()
        // DeepSeek is urgent → should beat Claude's `topup`.
        store.apply(QuotaResponse(
            packages: [
                pkg("a1", brand: "Claude", slug: "claude", alert: "topup", ratio: 0.72),
                pkg("b1", brand: "DeepSeek", slug: "deepseek", alert: "urgent", ratio: 0.92),
                pkg("c1", brand: "Gemini", slug: "gemini", alert: "ok", ratio: 0.05),
            ],
            byAlert: nil, catalogSuggestions: nil, skippedPackages: nil
        ))
        #expect(store.brands.map { $0.brandSlug } == ["deepseek", "claude", "gemini"])
    }

    @Test func tiesBreakByMaxUsedRatioThenName() {
        let store = makeStore()
        store.apply(QuotaResponse(
            packages: [
                pkg("a1", brand: "Bravo", slug: "bravo", alert: "watch", ratio: 0.55),
                pkg("a2", brand: "Alpha", slug: "alpha", alert: "watch", ratio: 0.65),
                pkg("a3", brand: "Charlie", slug: "charlie", alert: "watch", ratio: 0.55),
            ],
            byAlert: nil, catalogSuggestions: nil, skippedPackages: nil
        ))
        #expect(store.brands.map { $0.brand } == ["Alpha", "Bravo", "Charlie"])
    }

    @Test func menuBarSummaryPicksTightestWindow() {
        let store = makeStore()
        store.apply(QuotaResponse(
            packages: [
                pkg("a1", brand: "Claude", slug: "claude", alert: "topup", ratio: 0.72),
                pkg("b1", brand: "DeepSeek", slug: "deepseek", alert: "urgent", ratio: 0.94),
                pkg("c1", brand: "Gemini", slug: "gemini", alert: "ok", ratio: 0.05),
            ],
            byAlert: nil, catalogSuggestions: nil, skippedPackages: nil
        ))
        let summary = store.menuBarSummary
        #expect(summary.label == "fAI · 94%")
        #expect(summary.alert == .urgent)
    }

    @Test func menuBarSummaryEmptyFallsBackToIdle() {
        let store = makeStore()
        store.apply(QuotaResponse(
            packages: [], byAlert: nil, catalogSuggestions: nil, skippedPackages: nil
        ))
        let summary = store.menuBarSummary
        #expect(summary.label == "fAI")
        #expect(summary.alert == .ok)
    }

    @Test func identityComesFromFirstPackage() {
        let store = makeStore()
        let identity = Identity(loginMethod: "OAuth", credential: "claude-code")
        store.apply(QuotaResponse(
            packages: [
                pkg("a1", brand: "Claude", slug: "claude", alert: "ok", ratio: 0.2, identity: identity),
                pkg("a2", brand: "Claude", slug: "claude", alert: "watch", ratio: 0.6),
            ],
            byAlert: nil, catalogSuggestions: nil, skippedPackages: nil
        ))
        #expect(store.brands.first?.identity == identity)
    }
}
