import SwiftUI

/// The menubar popover contents. Mirrors the web widget's page composition:
///
///   1. Active brand cards (sorted worst-alert first).
///   2. A mini catalog "Available to add" block.
///   3. A footer with Cockpit + Refresh controls.
///
/// Skipped-package block is collapsed into a subtle footer line to keep the
/// popover short; the web widget is the place to inspect skipped entries in
/// detail.
struct PopoverView: View {
    @ObservedObject var store: QuotaStore
    @ObservedObject var preferences: Preferences
    /// Parent (the MenuBarExtra scene) owns the settings window-presentation
    /// so this view just signals intent.
    var onOpenPreferences: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            header
            Divider().background(Theme.border)
            content
            Divider().background(Theme.border)
            footer
        }
        .frame(width: 360)
        .frame(minHeight: 200, maxHeight: 640)
        .background(Theme.background)
        .foregroundColor(Theme.foreground)
    }

    // MARK: - Header

    private var header: some View {
        HStack(alignment: .center, spacing: 8) {
            Text("fusionAIze Gate Bar")
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(Theme.foreground)
            Spacer(minLength: 8)
            if store.isLoading {
                ProgressView()
                    .controlSize(.small)
            }
            Text(lastRefreshLabel)
                .font(.system(size: 10))
                .foregroundColor(Theme.dim)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
    }

    private var lastRefreshLabel: String {
        guard let refreshed = store.lastRefresh else {
            return store.lastError == nil ? "never refreshed" : "offline"
        }
        let f = RelativeDateTimeFormatter()
        f.unitsStyle = .short
        return "updated \(f.localizedString(for: refreshed, relativeTo: Date()))"
    }

    // MARK: - Main content

    @ViewBuilder
    private var content: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 10) {
                if let error = store.lastError {
                    errorBanner(error)
                }
                if store.brands.isEmpty && store.lastError == nil {
                    emptyBanner
                } else {
                    ForEach(store.brands) { brand in
                        BrandCardView(brand: brand)
                    }
                }
                if !store.catalogSuggestions.isEmpty {
                    catalogBlock
                }
                if !store.skippedPackages.isEmpty {
                    skippedBlock
                }
            }
            .padding(.horizontal, 12)
            .padding(.vertical, 12)
        }
    }

    private var emptyBanner: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("No active providers")
                .font(.system(size: 12, weight: .semibold))
            Text("Start the faigate gateway or check the gateway URL in Preferences.")
                .font(.system(size: 11))
                .foregroundColor(Theme.dim)
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.card)
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }

    private func errorBanner(_ message: String) -> some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Can't reach the gateway")
                .font(.system(size: 12, weight: .semibold))
                .foregroundColor(Theme.color(for: .urgent))
            Text(message)
                .font(.system(size: 11))
                .foregroundColor(Theme.dim)
                .lineLimit(3)
        }
        .padding(10)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(Theme.card)
        .overlay(
            RoundedRectangle(cornerRadius: 6)
                .strokeBorder(Theme.color(for: .urgent).opacity(0.5), lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 6))
    }

    // Design doc §3.3: max 6 rows, anything past collapses into "N more".
    private var catalogBlock: some View {
        VStack(alignment: .leading, spacing: 6) {
            Text("Available to add")
                .font(.system(size: 11, weight: .semibold))
                .foregroundColor(Theme.dim)
                .textCase(.uppercase)
                .padding(.top, 4)
            ForEach(store.catalogSuggestions.prefix(6)) { suggestion in
                HStack(alignment: .firstTextBaseline) {
                    Text(suggestion.brand)
                        .font(.system(size: 12, weight: .medium))
                        .foregroundColor(Theme.foreground)
                    Text(suggestion.tagline)
                        .font(.system(size: 11))
                        .foregroundColor(Theme.dim)
                        .lineLimit(1)
                    Spacer(minLength: 8)
                    Link("Add ↗", destination: cockpitLink(for: suggestion.brandSlug, path: "providers/add"))
                        .font(.system(size: 11))
                        .foregroundColor(Theme.link)
                }
            }
            if store.catalogSuggestions.count > 6 {
                let extra = store.catalogSuggestions.count - 6
                Link("… \(extra) more in Cockpit ↗", destination: cockpitLink())
                    .font(.system(size: 11))
                    .foregroundColor(Theme.link)
            }
        }
    }

    private var skippedBlock: some View {
        Text("Skipped: \(store.skippedPackages.map { $0.brand ?? $0.packageId }.joined(separator: ", "))")
            .font(.system(size: 10))
            .foregroundColor(Theme.dim)
            .lineLimit(2)
            .padding(.top, 4)
    }

    // MARK: - Footer

    private var footer: some View {
        HStack(spacing: 12) {
            Link(destination: cockpitLink()) {
                Text("Cockpit ↗")
                    .font(.system(size: 12))
            }
            .foregroundColor(Theme.link)

            Button {
                Task { await store.refresh() }
            } label: {
                Text("Refresh")
                    .font(.system(size: 12))
            }
            .buttonStyle(.plain)
            .foregroundColor(Theme.link)

            Spacer()

            Button {
                onOpenPreferences()
            } label: {
                Text("Preferences…")
                    .font(.system(size: 12))
            }
            .buttonStyle(.plain)
            .foregroundColor(Theme.dim)

            Button {
                NSApp.terminate(nil)
            } label: {
                Text("Quit")
                    .font(.system(size: 12))
            }
            .buttonStyle(.plain)
            .foregroundColor(Theme.dim)
        }
        .padding(.horizontal, 14)
        .padding(.vertical, 10)
    }

    private func cockpitLink(for brandSlug: String? = nil, path: String? = nil) -> URL {
        let base = preferences.cockpitURL.hasSuffix("/")
            ? String(preferences.cockpitURL.dropLast())
            : preferences.cockpitURL
        if let brandSlug, let path {
            let encoded = brandSlug.addingPercentEncoding(withAllowedCharacters: .urlPathAllowed) ?? brandSlug
            return URL(string: "\(base)/\(path)?brand=\(encoded)") ?? URL(string: base)!
        }
        if let path {
            return URL(string: "\(base)/\(path)") ?? URL(string: base)!
        }
        return URL(string: base) ?? URL(string: "https://cockpit.fusionaize.ai")!
    }
}
