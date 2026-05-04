import SwiftUI

/// Card for a single provider in the "Töpfe" (real-quota) view.
/// Mirrors the visual language of BrandCardView but driven by
/// ProviderSnapshot data from fetch_quotas.py.
struct ProviderCardView: View {
    let snapshot: ProviderSnapshot

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            header
            if let err = snapshot.error {
                Text(err)
                    .font(.system(size: 11))
                    .foregroundColor(Theme.color(for: .urgent))
                    .lineLimit(2)
            } else {
                ForEach(Array(snapshot.windows.enumerated()), id: \.element.id) { idx, win in
                    if idx > 0 { Divider().background(Theme.border).padding(.vertical, 2) }
                    WindowRow(window: win)
                }
                if let credits = snapshot.credits {
                    if !snapshot.windows.isEmpty {
                        Divider().background(Theme.border).padding(.vertical, 2)
                    }
                    CreditsRow(credits: credits)
                }
            }
        }
        .padding(.vertical, 10)
        .padding(.horizontal, 12)
        .background(Theme.card)
        .overlay(
            Rectangle()
                .fill(snapshot.error != nil ? Theme.color(for: .urgent) : Theme.accent.opacity(0.6))
                .frame(width: 3),
            alignment: .leading
        )
        .overlay(RoundedRectangle(cornerRadius: 8).strokeBorder(Theme.border, lineWidth: 1))
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var header: some View {
        Text(snapshot.brand)
            .font(.system(size: 15, weight: .semibold))
            .foregroundColor(Theme.foreground)
    }
}

/// One usage window row (e.g. "Session (5h)" with a progress bar).
private struct WindowRow: View {
    let window: UsageWindow

    private var usedRatio: Double { max(0, min(1, window.usedPct / 100)) }

    private var alert: AlertLevel {
        switch usedRatio {
        case 1...:    return .exhausted
        case 0.9...:  return .urgent
        case 0.75...: return .topup
        case 0.5...:  return .watch
        default:      return .ok
        }
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .firstTextBaseline) {
                Text(window.label)
                    .font(.system(size: 13))
                    .foregroundColor(Theme.mid)
                Spacer(minLength: 8)
                Text(pctLabel)
                    .font(.system(size: 12, weight: .semibold, design: .monospaced))
                    .foregroundColor(Theme.foreground)
            }
            bar
            if let reset = resetLabel {
                Text(reset)
                    .font(.system(size: 11))
                    .foregroundColor(Theme.dim)
            }
        }
    }

    private var pctLabel: String {
        let p = window.usedPct
        return p < 10 ? String(format: "%.1f%%", p) : "\(Int(p.rounded()))%"
    }

    private var resetLabel: String? {
        guard let iso = window.resetsAt, !iso.isEmpty else { return nil }
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        let date = formatter.date(from: iso) ?? {
            formatter.formatOptions = [.withInternetDateTime]
            return formatter.date(from: iso)
        }()
        guard let date else { return "resets \(iso.prefix(10))" }
        let rel = RelativeDateTimeFormatter()
        rel.unitsStyle = .short
        return "resets \(rel.localizedString(for: date, relativeTo: Date()))"
    }

    private var bar: some View {
        GeometryReader { proxy in
            ZStack(alignment: .topLeading) {
                Capsule().fill(Theme.track)
                Capsule()
                    .fill(Theme.color(for: alert))
                    .frame(width: proxy.size.width * usedRatio)
            }
        }
        .frame(height: 7)
    }
}

/// Credits / spend row (no progress bar for PAYG; bar for pre-paid).
private struct CreditsRow: View {
    let credits: CreditsInfo

    var body: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(credits.isPayg ? "Spend" : "Credits")
                .font(.system(size: 13))
                .foregroundColor(Theme.mid)
            Spacer(minLength: 8)
            if credits.isPayg {
                Text(String(format: "$%.4f %@", credits.used, credits.currency))
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundColor(Theme.dim)
            } else if let total = credits.total, let pct = credits.usedPct {
                Text(String(format: "%.2f / %.2f %@ (%.0f%%)",
                            credits.used, total, credits.currency, pct))
                    .font(.system(size: 12, design: .monospaced))
                    .foregroundColor(Theme.dim)
            }
        }
    }
}
