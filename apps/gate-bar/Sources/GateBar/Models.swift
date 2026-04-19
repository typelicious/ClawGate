import Foundation

// MARK: - JSON models (mirror /api/quotas)
//
// These intentionally decode a *subset* of the gateway's response — only the
// fields the menubar actually renders. Extra fields in the JSON are ignored,
// so the Python side can add new fields without breaking Gate Bar.
//
// Contract source of truth: `faigate.quota_tracker.QuotaStatus.to_dict()` and
// the `/api/quotas` handler in `faigate/main.py`. Keep field names in sync.

/// Top-level response from `GET /api/quotas`.
struct QuotaResponse: Decodable {
    let packages: [QuotaPackage]
    let byAlert: [String: Int]?
    let catalogSuggestions: [CatalogSuggestion]?
    let skippedPackages: [SkippedPackage]?

    enum CodingKeys: String, CodingKey {
        case packages
        case byAlert = "by_alert"
        case catalogSuggestions = "catalog_suggestions"
        case skippedPackages = "skipped_packages"
    }
}

/// One active package. The menubar groups these by `brandSlug` into cards.
struct QuotaPackage: Decodable, Identifiable {
    let packageId: String
    let providerId: String?
    let providerGroup: String?

    // v1.3 brand pivot (see docs/GATE-BAR-DESIGN.md §1).
    let brand: String
    let brandSlug: String
    let identity: Identity?

    let packageType: String?
    let usedRatio: Double?
    let elapsedRatio: Double?
    let paceDelta: Double?
    let alert: String?
    let resetAt: String?
    let projectedDaysLeft: Double?

    // Human-readable numerators/denominators for the under-bar line.
    let usedDisplay: String?
    let totalDisplay: String?

    // The dashboard labels each row by `package_name` (authored) — fall back
    // to package_id when the catalog is pre-v1.3 or the field is missing.
    let packageName: String?

    var id: String { packageId }

    enum CodingKeys: String, CodingKey {
        case packageId = "package_id"
        case providerId = "provider_id"
        case providerGroup = "provider_group"
        case brand
        case brandSlug = "brand_slug"
        case identity
        case packageType = "package_type"
        case usedRatio = "used_ratio"
        case elapsedRatio = "elapsed_ratio"
        case paceDelta = "pace_delta"
        case alert
        case resetAt = "reset_at"
        case projectedDaysLeft = "projected_days_left"
        case usedDisplay = "used_display"
        case totalDisplay = "total_display"
        case packageName = "package_name"
    }
}

/// Credential identity the operator sees under each brand header.
/// Always one of two shapes — env-var-style API key or OAuth subject.
struct Identity: Decodable, Equatable {
    let loginMethod: String
    let credential: String

    enum CodingKeys: String, CodingKey {
        case loginMethod = "login_method"
        case credential
    }
}

/// Catalog row the widget offers as "Available to add". Shape matches
/// `/api/quotas.catalog_suggestions`.
struct CatalogSuggestion: Decodable, Identifiable, Hashable {
    let brand: String
    let brandSlug: String
    let tagline: String

    var id: String { brandSlug }

    enum CodingKeys: String, CodingKey {
        case brand
        case brandSlug = "brand_slug"
        case tagline
    }
}

/// Inactive packages shown in the "Skipped" section (credential missing).
struct SkippedPackage: Decodable, Identifiable, Hashable {
    let packageId: String
    let brand: String?
    let brandSlug: String?
    let requires: String?

    var id: String { packageId }

    enum CodingKeys: String, CodingKey {
        case packageId = "package_id"
        case brand
        case brandSlug = "brand_slug"
        case requires
    }
}

// MARK: - Derived aggregates

/// A brand card as rendered in the popover: every package for that brand,
/// plus the identity line (pulled from the first package — identity is
/// brand-wide by design).
struct BrandGroup: Identifiable, Hashable {
    let brand: String
    let brandSlug: String
    let identity: Identity?
    let packages: [QuotaPackage]

    var id: String { brandSlug }

    /// Worst `used_ratio` across this brand's packages. Drives card sort
    /// order so the brand most likely to blow up is rendered first.
    var maxUsedRatio: Double {
        packages.compactMap { $0.usedRatio }.max() ?? 0
    }

    /// Highest alert severity across the brand.
    var worstAlert: AlertLevel {
        packages.map { AlertLevel(rawAlert: $0.alert, usedRatio: $0.usedRatio) }
            .max(by: { $0.severity < $1.severity }) ?? .ok
    }

    static func == (lhs: BrandGroup, rhs: BrandGroup) -> Bool {
        lhs.brandSlug == rhs.brandSlug && lhs.packages.map { $0.packageId } == rhs.packages.map { $0.packageId }
    }

    func hash(into hasher: inout Hasher) {
        hasher.combine(brandSlug)
        hasher.combine(packages.map { $0.packageId })
    }
}

/// Severity levels that drive the progress-bar colour and the menubar dot.
/// Ordered so `max(by:)` picks "worst".
enum AlertLevel: String, Comparable {
    case ok
    case watch
    case topup
    case urgent
    case exhausted

    var severity: Int {
        switch self {
        case .ok: return 0
        case .watch: return 1
        case .topup: return 2
        case .urgent: return 3
        case .exhausted: return 4
        }
    }

    static func < (lhs: AlertLevel, rhs: AlertLevel) -> Bool {
        lhs.severity < rhs.severity
    }

    /// Classify a package. Prefers the server-labelled alert; falls back to
    /// `used_ratio` thresholds (kept in sync with the widget's `classify()`
    /// in `_QUOTAS_DASHBOARD_HTML`).
    init(rawAlert: String?, usedRatio: Double?) {
        if let raw = rawAlert, let level = AlertLevel(rawValue: raw) {
            self = level
            return
        }
        let pct = max(0, min(1, usedRatio ?? 0))
        switch pct {
        case 1.0...: self = .exhausted
        case 0.9...: self = .urgent
        case 0.7...: self = .topup
        case 0.5...: self = .watch
        default: self = .ok
        }
    }
}
