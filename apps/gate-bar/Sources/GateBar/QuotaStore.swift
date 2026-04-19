import Foundation
import Combine

/// Source of truth for the Gate Bar menubar & popover.
///
/// Fetches `/api/quotas` on a timer (cadence driven by `Preferences`),
/// exposes three observable shapes the UI reads:
///
///   - ``brands`` — grouped, sorted brand cards for the popover.
///   - ``catalogSuggestions`` / ``skippedPackages`` — tail blocks.
///   - ``menuBarSummary`` — the label + colour the menubar displays.
///
/// `ObservableObject` + `@Published` so the app compiles on Sonoma without
/// the Observation framework.
@MainActor
final class QuotaStore: ObservableObject {
    @Published private(set) var brands: [BrandGroup] = []
    @Published private(set) var catalogSuggestions: [CatalogSuggestion] = []
    @Published private(set) var skippedPackages: [SkippedPackage] = []

    /// Last refresh attempt's result. `nil` means "never fetched yet".
    @Published private(set) var lastError: String? = nil
    @Published private(set) var lastRefresh: Date? = nil
    @Published private(set) var isLoading: Bool = false

    private let client: QuotaClient
    private let preferences: Preferences
    private var timerCancellable: AnyCancellable?
    private var prefsCancellable: AnyCancellable?

    init(client: QuotaClient = QuotaClient(), preferences: Preferences) {
        self.client = client
        self.preferences = preferences

        // Re-arm the timer whenever the refresh preference changes.
        self.prefsCancellable = preferences.$refreshInterval
            .sink { [weak self] interval in
                self?.rearmTimer(interval: interval)
            }
    }

    /// Fetch once now. Idempotent; safe to call from the "Refresh now"
    /// menu item or on app launch.
    func refresh() async {
        isLoading = true
        defer { isLoading = false }
        do {
            let response = try await client.fetchQuotas(baseURL: preferences.gatewayURL)
            self.apply(response)
            self.lastError = nil
            self.lastRefresh = Date()
        } catch {
            self.lastError = (error as? LocalizedError)?.errorDescription
                ?? error.localizedDescription
        }
    }

    /// Rebuild the published shapes from a freshly decoded response.
    /// Kept non-private so tests can drive the store without real HTTP.
    func apply(_ response: QuotaResponse) {
        // Group by brand_slug, preserving the server's package order within
        // each card. Sorting is done in a second pass so the "worst alert
        // first" rule is explicit and testable.
        var grouped: [String: (brand: String, identity: Identity?, pkgs: [QuotaPackage])] = [:]
        var order: [String] = []
        for pkg in response.packages {
            if grouped[pkg.brandSlug] == nil {
                grouped[pkg.brandSlug] = (pkg.brand, pkg.identity, [])
                order.append(pkg.brandSlug)
            }
            grouped[pkg.brandSlug]?.pkgs.append(pkg)
        }

        let unsorted: [BrandGroup] = order.compactMap { slug in
            guard let entry = grouped[slug] else { return nil }
            return BrandGroup(
                brand: entry.brand,
                brandSlug: slug,
                identity: entry.identity,
                packages: entry.pkgs
            )
        }

        // Worst severity → highest usage → alphabetical. Keeps the card the
        // operator most likely needs to act on at the top of the popover.
        self.brands = unsorted.sorted { a, b in
            if a.worstAlert != b.worstAlert {
                return a.worstAlert > b.worstAlert
            }
            if a.maxUsedRatio != b.maxUsedRatio {
                return a.maxUsedRatio > b.maxUsedRatio
            }
            return a.brand.localizedCaseInsensitiveCompare(b.brand) == .orderedAscending
        }

        self.catalogSuggestions = response.catalogSuggestions ?? []
        self.skippedPackages = response.skippedPackages ?? []
    }

    // MARK: - Menubar summary

    /// Tightest-window percentage across every active package, plus the
    /// worst alert level (drives the menubar colour dot).
    /// ``label`` is always short enough to fit the macOS menubar (≤ 12 chars).
    struct MenuBarSummary: Equatable {
        let label: String
        let alert: AlertLevel
    }

    var menuBarSummary: MenuBarSummary {
        let ratios = brands.flatMap { $0.packages }
            .compactMap { $0.usedRatio }
        guard let tightest = ratios.max() else {
            return MenuBarSummary(label: "fAI", alert: .ok)
        }
        let worst = brands.map { $0.worstAlert }.max() ?? .ok
        let pct = Int((max(0, min(1, tightest)) * 100).rounded())
        return MenuBarSummary(label: "fAI · \(pct)%", alert: worst)
    }

    // MARK: - Timer

    private func rearmTimer(interval: Preferences.RefreshInterval) {
        timerCancellable?.cancel()
        timerCancellable = nil
        guard interval != .manual else { return }
        let seconds = TimeInterval(interval.rawValue)
        timerCancellable = Timer.publish(every: seconds, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in
                Task { [weak self] in await self?.refresh() }
            }
    }
}
