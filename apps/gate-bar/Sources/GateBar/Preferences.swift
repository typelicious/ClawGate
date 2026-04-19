import Foundation

/// User-visible preferences, persisted via `UserDefaults`.
///
/// Uses `@Published` + `ObservableObject` per the design doc (§2, "no
/// `Observable`-only APIs — use `ObservableObject`") so the app builds on
/// macOS 14 Sonoma without needing the Observation framework.
final class Preferences: ObservableObject {
    // Refresh cadence. CodexBar defaults to 5 min; we keep that (design doc
    // §2.6). Manual = never auto-refresh.
    enum RefreshInterval: Int, CaseIterable, Identifiable {
        case manual = 0
        case oneMinute = 60
        case twoMinutes = 120
        case fiveMinutes = 300
        case fifteenMinutes = 900

        var id: Int { rawValue }

        var displayName: String {
            switch self {
            case .manual: return "Manual"
            case .oneMinute: return "Every 1 min"
            case .twoMinutes: return "Every 2 min"
            case .fiveMinutes: return "Every 5 min"
            case .fifteenMinutes: return "Every 15 min"
            }
        }
    }

    // Defaults suite — use standard so `defaults write com.fusionaize.gate-bar`
    // can tweak settings without opening the preferences window.
    private let defaults: UserDefaults
    private enum Key {
        static let gatewayURL = "gatewayURL"
        static let refreshInterval = "refreshIntervalSeconds"
        static let cockpitURL = "cockpitURL"
    }

    @Published var gatewayURL: String {
        didSet { defaults.set(gatewayURL, forKey: Key.gatewayURL) }
    }

    @Published var cockpitURL: String {
        didSet { defaults.set(cockpitURL, forKey: Key.cockpitURL) }
    }

    @Published var refreshInterval: RefreshInterval {
        didSet { defaults.set(refreshInterval.rawValue, forKey: Key.refreshInterval) }
    }

    /// Safe defaults that Just Work on a fresh install.
    /// Gateway default matches faigate's listen port (4001).
    /// Cockpit default matches `_cockpit_base_url()` in the Python side.
    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        self.gatewayURL = defaults.string(forKey: Key.gatewayURL)
            ?? "http://127.0.0.1:4001"
        self.cockpitURL = defaults.string(forKey: Key.cockpitURL)
            ?? "https://cockpit.fusionaize.ai"
        let rawInterval = defaults.object(forKey: Key.refreshInterval) as? Int
        self.refreshInterval = RefreshInterval(rawValue: rawInterval ?? 300)
            ?? .fiveMinutes
    }
}
