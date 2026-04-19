import Foundation

/// HTTP client for the local faigate gateway.
///
/// Everything Gate Bar knows about its providers comes from this one
/// endpoint — the Python side is already the source of truth. That
/// discipline (see `docs/GATE-BAR-DESIGN.md` §5) keeps the menubar app free
/// of a hard-coded provider enum and lets the catalog evolve without a Gate
/// Bar release.
actor QuotaClient {
    enum ClientError: LocalizedError {
        case invalidURL(String)
        case transport(Error)
        case httpStatus(Int)
        case decoding(Error)

        var errorDescription: String? {
            switch self {
            case .invalidURL(let raw):
                return "Gateway URL is not valid: \(raw)"
            case .transport(let err):
                // Network errors get the URLError localized description —
                // friendlier than the raw NSError string.
                return (err as? URLError)?.localizedDescription
                    ?? err.localizedDescription
            case .httpStatus(let code):
                return "Gateway returned HTTP \(code)"
            case .decoding:
                return "Gateway response did not match the expected shape"
            }
        }
    }

    private let session: URLSession
    private let decoder: JSONDecoder

    init(session: URLSession = .shared) {
        self.session = session
        // Ignoring unknown keys is the default for Swift Decodable — nothing
        // to configure there. We *do* want to parse ISO-8601 timestamps
        // (`reset_at`) to Date eventually, but the UI renders them as
        // strings today so we keep the decoder simple.
        self.decoder = JSONDecoder()
    }

    /// Fetch the current quota snapshot.
    ///
    /// - Parameter baseURL: `http://127.0.0.1:<port>` (no trailing slash
    ///   required — the `/api/quotas` path is appended via URLComponents so
    ///   trailing slashes, query strings, etc. are all tolerated).
    func fetchQuotas(baseURL: String) async throws -> QuotaResponse {
        guard var components = URLComponents(string: baseURL) else {
            throw ClientError.invalidURL(baseURL)
        }
        // Normalize path: ``/api/quotas`` regardless of the user's trailing
        // slash habits. ``URL(string:relativeTo:)`` would drop a non-empty
        // base path, which we don't want.
        components.path = (components.path.hasSuffix("/")
            ? components.path + "api/quotas"
            : components.path + "/api/quotas")
        components.query = nil

        guard let url = components.url else {
            throw ClientError.invalidURL(baseURL)
        }

        var request = URLRequest(url: url)
        request.timeoutInterval = 8
        request.httpMethod = "GET"
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("fusionaize-gate-bar", forHTTPHeaderField: "User-Agent")

        let (data, response): (Data, URLResponse)
        do {
            (data, response) = try await session.data(for: request)
        } catch {
            throw ClientError.transport(error)
        }

        if let http = response as? HTTPURLResponse, !(200..<300).contains(http.statusCode) {
            throw ClientError.httpStatus(http.statusCode)
        }

        do {
            return try decoder.decode(QuotaResponse.self, from: data)
        } catch {
            throw ClientError.decoding(error)
        }
    }
}
