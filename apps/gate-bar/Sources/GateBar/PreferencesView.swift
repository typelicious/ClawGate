import SwiftUI

/// The Preferences window. Intentionally minimal — four controls, no
/// wizards. See docs/GATE-BAR-DESIGN.md §5 ("Preferences window").
struct PreferencesView: View {
    @ObservedObject var preferences: Preferences

    var body: some View {
        Form {
            Section("Gateway") {
                TextField("Gateway URL", text: $preferences.gatewayURL)
                    .textFieldStyle(.roundedBorder)
                    .frame(minWidth: 260)
                Text("The local faigate daemon, typically http://127.0.0.1:4001.")
                    .font(.footnote)
                    .foregroundColor(.secondary)
            }

            Section("Operator Cockpit") {
                TextField("Cockpit URL", text: $preferences.cockpitURL)
                    .textFieldStyle(.roundedBorder)
                    .frame(minWidth: 260)
                Text("Opens in your default browser when you click Cockpit ↗.")
                    .font(.footnote)
                    .foregroundColor(.secondary)
            }

            Section("Refresh") {
                Picker("Refresh interval", selection: $preferences.refreshInterval) {
                    ForEach(Preferences.RefreshInterval.allCases) { interval in
                        Text(interval.displayName).tag(interval)
                    }
                }
                .pickerStyle(.menu)
            }

            Section("Privacy") {
                // Verbatim from the about-box copy in docs/GATE-BAR-DESIGN.md §5.
                Text(
                    """
                    Gate Bar reads usage data from your local fusionAIze Gate \
                    daemon over 127.0.0.1. Account identifiers, plan names, \
                    and login methods stay on this machine. Gate Bar never \
                    connects to a fusionAIze-hosted service; the Cockpit link \
                    just opens a web page in your default browser.
                    """
                )
                .font(.footnote)
                .foregroundColor(.secondary)
                .fixedSize(horizontal: false, vertical: true)
            }
        }
        .formStyle(.grouped)
        .frame(width: 420)
        .frame(minHeight: 380)
    }
}
