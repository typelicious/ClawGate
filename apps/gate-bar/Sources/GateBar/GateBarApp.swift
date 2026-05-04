import SwiftUI
import AppKit
import Combine

/// fusionAIze Gate Bar — macOS menubar companion.
///
/// The app runs as an agent (`LSUIElement=true`) and owns a single
/// `NSStatusItem` plus a custom `NSPanel` for the popover. We explicitly
/// position the panel flush to the right edge of the screen, just below
/// the menubar — SwiftUI's `MenuBarExtra` anchors under the icon and
/// offers no override, so we drop down a level to AppKit for this.
///
/// Preferences are still a stock SwiftUI `Settings` scene; opening it goes
/// through `NSApp.sendAction(Selector(("showSettingsWindow:")))` which is
/// the documented Sonoma API.
@main
struct GateBarApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var appDelegate

    var body: some Scene {
        Settings {
            PreferencesView(preferences: appDelegate.preferences)
        }
    }
}

/// Owns the status item, the popover panel, and the quota store.
///
/// Lives for the app's whole lifetime via ``GateBarApp``'s
/// ``@NSApplicationDelegateAdaptor``. Exposes ``preferences`` so the
/// SwiftUI Settings scene can bind to the same instance the store reads.
@MainActor
final class AppDelegate: NSObject, NSApplicationDelegate, ObservableObject {
    let preferences = Preferences()
    lazy var store: QuotaStore = QuotaStore(preferences: preferences)
    lazy var helperStore: QuotaHelperStore = QuotaHelperStore(providers: ["claude", "openrouter"])

    private var statusItem: NSStatusItem?
    private var panel: NSPanel?
    private var preferencesWindow: NSWindow?
    private var globalMonitor: Any?
    private var localMonitor: Any?
    private var cancellables = Set<AnyCancellable>()

    func applicationDidFinishLaunching(_ notification: Notification) {
        // LSUIElement=true in Info.plist already hides the Dock icon, but
        // setting the activation policy explicitly is belt-and-braces for
        // devs launching the raw binary without the bundle.
        NSApp.setActivationPolicy(.accessory)
        setupStatusItem()
        setupPanel()
        observeStore()
    }

    // MARK: - Status item

    private func setupStatusItem() {
        let item = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        if let button = item.button {
            button.target = self
            button.action = #selector(togglePanel(_:))
            button.sendAction(on: [.leftMouseUp, .rightMouseUp])
        }
        statusItem = item
        updateStatusTitle(store.menuBarSummary)
    }

    /// Paints the menubar label: coloured dot + "fAI · 83%" in the menubar
    /// foreground colour. Using an `NSAttributedString` lets us colour just
    /// the dot without breaking macOS's automatic light/dark contrast on
    /// the rest of the text.
    private func updateStatusTitle(_ summary: QuotaStore.MenuBarSummary) {
        guard let button = statusItem?.button else { return }
        let attr = NSMutableAttributedString()
        attr.append(NSAttributedString(
            string: "●",
            attributes: [
                .foregroundColor: nsColor(for: summary.alert),
                .font: NSFont.systemFont(ofSize: 10, weight: .bold),
                .baselineOffset: 1,
            ]
        ))
        attr.append(NSAttributedString(
            string: " \(summary.label)",
            attributes: [
                .font: NSFont.monospacedSystemFont(ofSize: 12, weight: .medium),
            ]
        ))
        button.attributedTitle = attr
    }

    private func nsColor(for alert: AlertLevel) -> NSColor {
        switch alert {
        case .ok:        return NSColor(calibratedRed: 0.290, green: 0.871, blue: 0.502, alpha: 1)
        case .watch:     return NSColor(calibratedRed: 0.984, green: 0.749, blue: 0.141, alpha: 1)
        case .topup:     return NSColor(calibratedRed: 0.984, green: 0.573, blue: 0.235, alpha: 1)
        case .urgent:    return NSColor(calibratedRed: 0.937, green: 0.267, blue: 0.267, alpha: 1)
        case .exhausted: return NSColor(calibratedRed: 0.498, green: 0.114, blue: 0.114, alpha: 1)
        }
    }

    private func observeStore() {
        // Re-render the menubar label whenever anything the summary reads
        // can have changed. `menuBarSummary` is a computed property so we
        // just listen to the underlying `@Published` sources.
        Publishers.CombineLatest3(
            store.$brands,
            store.$lastError,
            store.$lastRefresh
        )
        .sink { [weak self] _, _, _ in
            guard let self else { return }
            self.updateStatusTitle(self.store.menuBarSummary)
        }
        .store(in: &cancellables)
    }

    // MARK: - Panel

    private func setupPanel() {
        let root = PopoverView(
            store: store,
            helperStore: helperStore,
            preferences: preferences,
            onOpenPreferences: { [weak self] in self?.openPreferences() }
        )
        let hosting = NSHostingController(rootView: root)

        // `.nonactivatingPanel` keeps focus in whatever app the operator
        // was using — a menubar utility shouldn't steal keyboard focus on
        // open. `.titled` + transparent titlebar gives SwiftUI room to
        // paint the whole rect itself.
        let panel = NSPanel(
            contentRect: NSRect(x: 0, y: 0, width: 440, height: 620),
            styleMask: [.titled, .fullSizeContentView, .nonactivatingPanel],
            backing: .buffered,
            defer: false
        )
        panel.contentViewController = hosting
        panel.titleVisibility = .hidden
        panel.titlebarAppearsTransparent = true
        panel.isMovable = false
        panel.isMovableByWindowBackground = false
        panel.level = .popUpMenu
        panel.hidesOnDeactivate = false
        panel.isReleasedWhenClosed = false
        panel.hasShadow = true
        panel.backgroundColor = .clear
        panel.standardWindowButton(.closeButton)?.isHidden = true
        panel.standardWindowButton(.miniaturizeButton)?.isHidden = true
        panel.standardWindowButton(.zoomButton)?.isHidden = true
        self.panel = panel
    }

    @objc private func togglePanel(_ sender: Any?) {
        guard let panel else { return }
        if panel.isVisible {
            closePanel()
        } else {
            openPanel()
        }
    }

    private func openPanel() {
        guard let panel else { return }
        // Position on whatever screen the menubar icon lives on. Falls
        // back to the main screen for single-display setups. `visibleFrame`
        // already excludes the menubar, so `maxY` is exactly the bottom
        // of the menubar — perfect for the panel's top edge.
        let screen = statusItem?.button?.window?.screen ?? NSScreen.main
        guard let visible = screen?.visibleFrame else { return }

        let size = panel.frame.size
        let margin: CGFloat = 8
        let x = visible.maxX - size.width - margin
        let y = visible.maxY - size.height
        panel.setFrameOrigin(NSPoint(x: x, y: y))
        panel.orderFrontRegardless()
        NSApp.activate(ignoringOtherApps: true)

        // Kick off a fresh fetch the moment the user opens the popover —
        // stale data is worse than a half-second loading spinner.
        Task {
            await store.refresh()
            await helperStore.refresh()
        }

        // Dismiss on click outside the panel, Esc closes it.
        globalMonitor = NSEvent.addGlobalMonitorForEvents(
            matching: [.leftMouseDown, .rightMouseDown]
        ) { [weak self] _ in
            self?.closePanel()
        }
        localMonitor = NSEvent.addLocalMonitorForEvents(matching: [.keyDown]) { [weak self] event in
            if event.keyCode == 53 { // Esc
                self?.closePanel()
                return nil
            }
            return event
        }
    }

    private func closePanel() {
        panel?.orderOut(nil)
        if let m = globalMonitor {
            NSEvent.removeMonitor(m)
            globalMonitor = nil
        }
        if let m = localMonitor {
            NSEvent.removeMonitor(m)
            localMonitor = nil
        }
    }

    // MARK: - Preferences

    /// Open Preferences in a dedicated NSWindow.
    ///
    /// We bypass SwiftUI's Settings scene routing entirely: with
    /// `.accessory` activation policy and a `nonactivatingPanel` popover
    /// already open, `showSettingsWindow:` never finds its target and
    /// silently drops the action. Direct NSWindow is guaranteed to work.
    func openPreferences() {
        if let existing = preferencesWindow, existing.isVisible {
            existing.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            return
        }
        let hosting = NSHostingController(rootView: PreferencesView(preferences: preferences))
        let window = NSWindow(contentViewController: hosting)
        window.title = "Gate Bar Preferences"
        window.styleMask = [.titled, .closable, .miniaturizable]
        window.isReleasedWhenClosed = false
        window.level = .floating
        window.center()
        preferencesWindow = window
        NSApp.activate(ignoringOtherApps: true)
        window.makeKeyAndOrderFront(nil)
    }
}
