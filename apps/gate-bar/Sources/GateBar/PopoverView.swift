import SwiftUI

/// The menubar popover. Two views selectable via a segment picker:
///
///   "Töpfe"  — real quota data fetched directly from provider web APIs
///              via fetch_quotas.py (Chrome cookies + faigate .env keys).
///   "faigate" — requests routed through the local faigate proxy, sourced
///              from /api/quotas on the gateway.
///
/// Both share the same header and footer; only the content scrollview
/// changes based on the selection.
struct PopoverView: View {
    @ObservedObject var store: QuotaStore
    @ObservedObject var helperStore: QuotaHelperStore
    @ObservedObject var preferences: Preferences
    var onOpenPreferences: () -> Void

    @State private var selectedView: PopoverTab = .topfe

    enum PopoverTab: String, CaseIterable {
        case topfe   = "Töpfe"
        case faigate = "faigate"
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            header
            Divider().background(Theme.border)
            content
            Divider().background(Theme.border)
            footer
        }
        .frame(width: 440)
        .frame(minHeight: 560, maxHeight: 1100)
        .background(Theme.background)
        .foregroundColor(Theme.foreground)
    }

    // MARK: - Header

    private var header: some View {
        VStack(spacing: 8) {
            HStack(alignment: .center, spacing: 8) {
                Text("fusionAIze Gate Bar")
                    .font(.system(size: 13, weight: .semibold))
                    .foregroundColor(Theme.foreground)
                Spacer(minLength: 8)
                if isLoading {
                    ProgressView().controlSize(.small)
                }
                Text(lastRefreshLabel)
                    .font(.system(size: 11))
                    .foregroundColor(Theme.dim)
            }
            Picker("View", selection: $selectedView) {
                ForEach(PopoverTab.allCases, id: \.self) { tab in
                    Text(tab.rawValue).tag(tab)
                }
            }
            .pickerStyle(.segmented)
        }
        .padding(.horizontal, 16)
        .padding(.top, 12)
        .padding(.bottom, 10)
    }

    private var isLoading: Bool {
        selectedView == .topfe ? helperStore.isLoading : store.isLoading
    }

    private var lastRefreshLabel: String {
        let refreshed = selectedView == .topfe ? helperStore.lastRefresh : store.lastRefresh
        let hasError  = selectedView == .topfe ? helperStore.lastError != nil : store.lastError != nil
        guard let refreshed else {
            return hasError ? "offline" : "never refreshed"
        }
        let f = RelativeDateTimeFormatter()
        f.unitsStyle = .short
        return "updated \(f.localizedString(for: refreshed, relativeTo: Date()))"
    }

    // MARK: - Content

    @ViewBuilder
    private var content: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                switch selectedView {
                case .topfe:   topfeContent
                case .faigate: faigateContent
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 12)
        }
    }

    // MARK: Töpfe view — real provider quotas

    @ViewBuilder
    private var topfeContent: some View {
        if let err = helperStore.lastError, helperStore.snapshots.isEmpty {
            errorBanner("fetch_quotas.py error", detail: err)
        } else if helperStore.snapshots.isEmpty {
            emptyBanner(
                title: "No provider data",
                detail: "Fetching quotas from your providers…"
            )
        } else {
            ForEach(helperStore.snapshots) { snap in
                ProviderCardView(snapshot: snap)
            }
        }
    }

    // MARK: faigate view — proxied traffic

    @ViewBuilder
    private var faigateContent: some View {
        if let error = store.lastError {
            errorBanner("Can't reach the gateway", detail: error)
        }
        if store.brands.isEmpty && store.lastError == nil {
            emptyBanner(
                title: "No active providers",
                detail: "Start the faigate gateway or check the gateway URL in Preferences."
            )
        } else {
            ForEach(store.brands) { brand in
                BrandCardView(brand: brand)
            }
        }
        if !store.catalogSuggestions.isEmpty { catalogBlock }
        if !store.skippedPackages.isEmpty    { skippedBlock }
    }

    // MARK: - Shared sub-views

    private func emptyBanner(title: String, detail: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title)
                .font(.system(size: 13, weight: .semibold))
            Text(detail)
                .font(.system(size: 12))
                .foregroundColor(Theme.dim)
        }
        .padding(14)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.card)
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }

    private func errorBanner(_ heading: String, detail: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(heading)
                .font(.system(size: 13, weight: .semibold))
                .foregroundColor(Theme.color(for: .urgent))
            Text(detail)
                .font(.system(size: 12))
                .foregroundColor(Theme.dim)
                .lineLimit(3)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.card)
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .strokeBorder(Theme.color(for: .urgent).opacity(0.5), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }

    private var catalogBlock: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Available to add")
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(Theme.dim)
                .textCase(.uppercase)
                .padding(.top, 6)
            ForEach(store.catalogSuggestions.prefix(6)) { suggestion in
                HStack(alignment: .firstTextBaseline) {
                    Text(suggestion.brand)
                        .font(.system(size: 13, weight: .medium))
                        .foregroundColor(Theme.foreground)
                    Text(suggestion.tagline)
                        .font(.system(size: 13))
                        .foregroundColor(Theme.dim)
                        .lineLimit(1)
                    Spacer(minLength: 8)
                    Link("Add ↗", destination: cockpitLink(for: suggestion.brandSlug, path: "providers/add"))
                        .font(.system(size: 13))
                        .foregroundColor(Theme.link)
                }
            }
            if store.catalogSuggestions.count > 6 {
                let extra = store.catalogSuggestions.count - 6
                Link("… \(extra) more in Cockpit ↗", destination: cockpitLink())
                    .font(.system(size: 13))
                    .foregroundColor(Theme.link)
            }
        }
    }

    private var skippedBlock: some View {
        Text("Skipped: \(store.skippedPackages.map { $0.brand ?? $0.packageId }.joined(separator: ", "))")
            .font(.system(size: 11))
            .foregroundColor(Theme.dim)
            .lineLimit(2)
            .padding(.top, 6)
    }

    // MARK: - Footer

    private var footer: some View {
        HStack(spacing: 12) {
            Link(destination: dashboardLink()) {
                Text("Dashboard ↗").font(.system(size: 13))
            }
            .foregroundColor(Theme.link)

            Link(destination: cockpitLink()) {
                Text("Cockpit ↗").font(.system(size: 13))
            }
            .foregroundColor(Theme.link)

            Button {
                Task {
                    await store.refresh()
                    await helperStore.refresh()
                }
            } label: {
                Text("Refresh").font(.system(size: 13))
            }
            .buttonStyle(.plain)
            .foregroundColor(Theme.link)

            Spacer()

            Button { onOpenPreferences() } label: {
                Text("Preferences…").font(.system(size: 13))
            }
            .buttonStyle(.plain)
            .foregroundColor(Theme.dim)

            Button { NSApp.terminate(nil) } label: {
                Text("Quit").font(.system(size: 13))
            }
            .buttonStyle(.plain)
            .foregroundColor(Theme.dim)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
    }

    // MARK: - URL helpers

    private func dashboardLink() -> URL {
        let base = preferences.gatewayURL.hasSuffix("/")
            ? String(preferences.gatewayURL.dropLast()) : preferences.gatewayURL
        return URL(string: "\(base)/dashboard/quotas") ?? URL(string: base)!
    }

    private func cockpitLink(for brandSlug: String? = nil, path: String? = nil) -> URL {
        let base = preferences.cockpitURL.hasSuffix("/")
            ? String(preferences.cockpitURL.dropLast()) : preferences.cockpitURL
        if let brandSlug, let path {
            let encoded = brandSlug.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? brandSlug
            return URL(string: "\(base)/\(path)?brand=\(encoded)") ?? URL(string: base)!
        }
        if let path { return URL(string: "\(base)/\(path)") ?? URL(string: base)! }
        return URL(string: base) ?? URL(string: "https://cockpit.fusionaize.ai")!
    }
}
