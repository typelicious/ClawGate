import SwiftUI

/// Colour palette mirroring the web widget's CSS variables in
/// `_QUOTAS_DASHBOARD_HTML`. Keeping them in one place means the menubar
/// popover visually reads as the same product as the browser dashboard.
enum Theme {
    static let background   = Color(red: 0.059, green: 0.067, blue: 0.090) // #0f1117
    static let card         = Color(red: 0.102, green: 0.114, blue: 0.153) // #1a1d27
    static let border       = Color(red: 0.165, green: 0.184, blue: 0.239) // #2a2f3d
    static let track        = Color(red: 0.149, green: 0.165, blue: 0.212) // #262a36

    static let foreground   = Color(red: 0.902, green: 0.914, blue: 0.937) // #e6e9ef
    static let mid          = Color(red: 0.725, green: 0.757, blue: 0.820) // #b9c1d1
    static let dim          = Color(red: 0.541, green: 0.576, blue: 0.651) // #8a93a6

    static let accent       = Color(red: 0.545, green: 0.361, blue: 0.965) // #8b5cf6
    static let link         = Color(red: 0.376, green: 0.647, blue: 0.980) // #60a5fa

    // Alert levels — keep in sync with AlertLevel.
    static func color(for alert: AlertLevel) -> Color {
        switch alert {
        case .ok:        return Color(red: 0.290, green: 0.871, blue: 0.502) // #4ade80
        case .watch:     return Color(red: 0.984, green: 0.749, blue: 0.141) // #fbbf24
        case .topup:     return Color(red: 0.984, green: 0.573, blue: 0.235) // #fb923c
        case .urgent:    return Color(red: 0.937, green: 0.267, blue: 0.267) // #ef4444
        case .exhausted: return Color(red: 0.498, green: 0.114, blue: 0.114) // #7f1d1d
        }
    }
}

/// Convenience for the "N · 83%" label — adds a coloured dot before the
/// text so the menubar reads at a glance even at low contrast.
struct AlertDot: View {
    let alert: AlertLevel
    var body: some View {
        Circle()
            .fill(Theme.color(for: alert))
            .frame(width: 8, height: 8)
    }
}
