import Foundation
import Combine

/// Runs fetch_quotas.py as a subprocess and publishes the parsed results.
///
/// The script path is resolved at init: first tries a bundle-relative
/// location (for when the helper is shipped alongside the .app), then
/// falls back to the dev-tree path so local builds work without any
/// extra setup.
@MainActor
final class QuotaHelperStore: ObservableObject {
    @Published private(set) var snapshots: [ProviderSnapshot] = []
    @Published private(set) var isLoading = false
    @Published private(set) var lastError: String? = nil
    @Published private(set) var lastRefresh: Date? = nil

    private let python3: String
    private let scriptPath: String
    private let providers: [String]
    private var timerCancellable: AnyCancellable?

    init(providers: [String] = ["claude", "openrouter"]) {
        self.providers = providers

        // python3 — prefer Homebrew arm64 install
        let pythonCandidates = [
            "/opt/homebrew/bin/python3",
            "/usr/local/bin/python3",
            "/usr/bin/python3",
        ]
        self.python3 = pythonCandidates.first {
            FileManager.default.fileExists(atPath: $0)
        } ?? "/usr/bin/python3"

        // fetch_quotas.py — bundle-relative first, dev-tree fallback
        let bundleScript = Bundle.main.path(forResource: "fetch_quotas", ofType: "py")
        let devScript = "/Users/andrelange/Documents/repositories/github/faigate/apps/quota-helper/fetch_quotas.py"
        self.scriptPath = bundleScript ?? devScript

        // Refresh every 5 minutes
        timerCancellable = Timer.publish(every: 300, on: .main, in: .common)
            .autoconnect()
            .sink { [weak self] _ in Task { [weak self] in await self?.refresh() } }
    }

    func refresh() async {
        guard FileManager.default.fileExists(atPath: scriptPath) else {
            lastError = "fetch_quotas.py not found at \(scriptPath)"
            return
        }
        isLoading = true
        defer { isLoading = false }
        do {
            let data = try await runScript()
            let decoded = try JSONDecoder().decode([ProviderSnapshot].self, from: data)
            self.snapshots = decoded
            self.lastError = nil
            self.lastRefresh = Date()
        } catch {
            self.lastError = error.localizedDescription
        }
    }

    private func runScript() async throws -> Data {
        try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.global(qos: .userInitiated).async { [python3, scriptPath, providers] in
                let process = Process()
                process.executableURL = URL(fileURLWithPath: python3)
                process.arguments = [scriptPath] + providers + ["--json-only"]

                // Inherit minimal PATH so the script finds system tools.
                var env = ProcessInfo.processInfo.environment
                env["PATH"] = "/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
                process.environment = env

                let stdout = Pipe()
                let stderr = Pipe()
                process.standardOutput = stdout
                process.standardError = stderr

                do {
                    try process.run()
                } catch {
                    continuation.resume(throwing: error)
                    return
                }
                process.waitUntilExit()
                let data = stdout.fileHandleForReading.readDataToEndOfFile()
                if data.isEmpty {
                    let errOut = String(data: stderr.fileHandleForReading.readDataToEndOfFile(), encoding: .utf8) ?? ""
                    continuation.resume(throwing: HelperError.emptyOutput(errOut))
                } else {
                    continuation.resume(returning: data)
                }
            }
        }
    }
}

enum HelperError: LocalizedError {
    case emptyOutput(String)
    var errorDescription: String? {
        switch self {
        case .emptyOutput(let detail): return "fetch_quotas.py produced no output. stderr: \(detail)"
        }
    }
}
