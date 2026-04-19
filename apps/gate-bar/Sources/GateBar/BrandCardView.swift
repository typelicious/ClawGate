import SwiftUI

/// A single brand card in the popover. Visual parity with the web
/// widget's `.brand` block in `_QUOTAS_DASHBOARD_HTML`:
///
///   - brand name left, identity right
///   - one `PackageRow` per package (bar + pace tick + % + under-bar meta)
///   - coloured left border carries the worst-alert signal
struct BrandCardView: View {
    let brand: BrandGroup

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            header
            ForEach(Array(brand.packages.enumerated()), id: \.element.packageId) { index, pkg in
                if index > 0 {
                    Divider()
                        .background(Theme.border)
                        .padding(.vertical, 2)
                }
                PackageRow(package: pkg)
            }
        }
        .padding(.vertical, 10)
        .padding(.horizontal, 12)
        .background(Theme.card)
        .overlay(
            Rectangle()
                .fill(Theme.color(for: brand.worstAlert))
                .frame(width: 3),
            alignment: .leading
        )
        .overlay(
            RoundedRectangle(cornerRadius: 8)
                .strokeBorder(Theme.border, lineWidth: 1)
        )
        .clipShape(RoundedRectangle(cornerRadius: 8))
    }

    private var header: some View {
        HStack(alignment: .firstTextBaseline) {
            Text(brand.brand)
                .font(.system(size: 14, weight: .semibold))
                .foregroundColor(Theme.foreground)
            Spacer(minLength: 8)
            if let identity = brand.identity {
                Text("\(identity.loginMethod): \(identity.credential)")
                    .font(.system(size: 10, design: .monospaced))
                    .foregroundColor(Theme.dim)
                    .lineLimit(1)
                    .truncationMode(.middle)
            }
        }
    }
}

/// One package inside a brand card.
///
/// Renders the same vocabulary as the web row:
///   - package title (left) + percentage (right)
///   - progress bar with an inline pace tick
///   - under-bar meta: `used / total` (left) · reset / days-left (right)
struct PackageRow: View {
    let package: QuotaPackage

    private var usedRatio: Double {
        max(0, min(1, package.usedRatio ?? 0))
    }

    private var alert: AlertLevel {
        AlertLevel(rawAlert: package.alert, usedRatio: package.usedRatio)
    }

    private var paceFraction: Double? {
        // Pace marker only makes sense when both sides of the computation
        // are present (rolling_window + daily). Credits packages return nil.
        guard package.paceDelta != nil, let elapsed = package.elapsedRatio else {
            return nil
        }
        return max(0, min(1, elapsed))
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            HStack(alignment: .firstTextBaseline) {
                Text(package.packageName ?? package.packageId)
                    .font(.system(size: 12))
                    .foregroundColor(Theme.mid)
                Spacer(minLength: 8)
                Text(percentageLabel)
                    .font(.system(size: 11, weight: .semibold, design: .monospaced))
                    .foregroundColor(Theme.foreground)
            }
            bar
            HStack {
                if let used = package.usedDisplay, let total = package.totalDisplay {
                    Text("\(used) / \(total)")
                        .font(.system(size: 10, design: .monospaced))
                        .foregroundColor(Theme.dim)
                }
                Spacer(minLength: 8)
                Text(resetLabel)
                    .font(.system(size: 10))
                    .foregroundColor(Theme.dim)
                    .lineLimit(1)
            }
        }
    }

    private var percentageLabel: String {
        let pct = usedRatio * 100
        if pct < 10 {
            return String(format: "%.1f%%", pct)
        }
        return "\(Int(pct.rounded()))%"
    }

    private var resetLabel: String {
        if let reset = package.resetAt, !reset.isEmpty {
            return "resets \(formatReset(reset))"
        }
        if let days = package.projectedDaysLeft {
            return "~\(Int(days.rounded()))d left"
        }
        return ""
    }

    private func formatReset(_ iso: String) -> String {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime]
        if let date = formatter.date(from: iso) ?? ISO8601DateFormatter.withFractional.date(from: iso) {
            let rel = RelativeDateTimeFormatter()
            rel.unitsStyle = .short
            return rel.localizedString(for: date, relativeTo: Date())
        }
        return iso
    }

    /// Progress bar with an inline pace tick. `GeometryReader` lets us
    /// position the tick at `elapsedRatio * width` without measuring text.
    private var bar: some View {
        GeometryReader { proxy in
            ZStack(alignment: .topLeading) {
                Capsule()
                    .fill(Theme.track)
                Capsule()
                    .fill(Theme.color(for: alert))
                    .frame(width: proxy.size.width * usedRatio)
                if let pace = paceFraction {
                    Rectangle()
                        .fill(Theme.accent)
                        .frame(width: 2, height: proxy.size.height + 4)
                        .offset(x: (proxy.size.width * pace) - 1, y: -2)
                }
            }
        }
        .frame(height: 6)
    }
}

private extension ISO8601DateFormatter {
    /// `/api/quotas` sometimes emits timestamps with fractional seconds
    /// depending on the backend; try both shapes.
    static let withFractional: ISO8601DateFormatter = {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        return f
    }()
}
