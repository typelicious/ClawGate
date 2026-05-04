import Foundation

/// Provider snapshot returned by fetch_quotas.py --json-only.
struct ProviderSnapshot: Decodable, Identifiable {
    var id: String { provider }
    let provider: String
    let brand: String
    let windows: [UsageWindow]
    let credits: CreditsInfo?
    let error: String?
}

struct UsageWindow: Decodable, Identifiable {
    var id: String { label }
    let label: String
    let usedPct: Double
    let resetsAt: String?

    enum CodingKeys: String, CodingKey {
        case label
        case usedPct = "used_pct"
        case resetsAt = "resets_at"
    }
}

struct CreditsInfo: Decodable {
    let used: Double
    let total: Double?
    let usedPct: Double?
    let currency: String
    let mode: String?

    enum CodingKeys: String, CodingKey {
        case used, total, currency, mode
        case usedPct = "used_pct"
    }

    var isPayg: Bool { mode == "payg" || total == nil }
}
