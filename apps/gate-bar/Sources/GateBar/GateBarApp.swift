import SwiftUI
import AppKit

/// fusionAIze Gate Bar — macOS menubar companion.
///
/// Entry point. The app is a `MenuBarExtra` (Sonoma 14+) with a
/// window-style popover and a separate Settings scene.
///
/// Note: `MenuBarExtra(_ :, isInserted:)` gives us a toggle for hiding the
/// icon entirely (future preference). The current cut always shows it.
@main
struct GateBarApp: App {
    @StateObject private var preferences = Preferences()
    @StateObject private var store: QuotaStore

    init() {
        let prefs = Preferences()
        _preferences = StateObject(wrappedValue: prefs)
        _store = StateObject(wrappedValue: QuotaStore(preferences: prefs))
    }

    var body: some Scene {
        MenuBarExtra {
            PopoverView(
                store: store,
                preferences: preferences,
                onOpenPreferences: { openPreferencesWindow() }
            )
            .task {
                // First fetch runs eagerly when the popover opens. A small
                // price for fresh data versus waiting for the timer.
                await store.refresh()
            }
        } label: {
            MenuBarLabelView(summary: store.menuBarSummary)
        }
        .menuBarExtraStyle(.window)

        Settings {
            PreferencesView(preferences: preferences)
        }
    }

    /// Programmatically open the Settings scene. The stock keyboard shortcut
    /// (``⌘,``) also works, but the "Preferences…" button in the popover
    /// footer gives a discoverable affordance.
    private func openPreferencesWindow() {
        NSApp.activate(ignoringOtherApps: true)
        if #available(macOS 14, *) {
            // Sonoma's standard Settings scene accepts this action.
            NSApp.sendAction(Selector(("showSettingsWindow:")), to: nil, from: nil)
        } else {
            NSApp.sendAction(Selector(("showPreferencesWindow:")), to: nil, from: nil)
        }
    }
}

/// The menubar label: a coloured dot + "fAI · 83%" text.
///
/// Rendered in the menubar's text colour so macOS keeps the contrast right
/// in both light and dark appearances.
struct MenuBarLabelView: View {
    let summary: QuotaStore.MenuBarSummary
    var body: some View {
        HStack(spacing: 4) {
            AlertDot(alert: summary.alert)
            Text(summary.label)
                .font(.system(size: 12, weight: .medium, design: .monospaced))
        }
    }
}
