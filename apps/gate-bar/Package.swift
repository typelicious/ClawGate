// swift-tools-version:5.9
//
// fusionAIze Gate Bar — macOS menubar companion for the faigate local gateway.
//
// Design anchors (see ../../docs/GATE-BAR-DESIGN.md §5):
//
//   - macOS 14 (Sonoma) minimum — keeps two-year-old Intel MacBooks alive.
//   - Universal binary (x86_64 + arm64). SPM handles this at release time via
//       swift build -c release --arch x86_64 --arch arm64
//   - SwiftUI surface is the Sonoma subset: ObservableObject, Combine, plain
//     Color. No @Observable, no MeshGradient.
//   - Pure HTTP consumer of the local gateway — no shared state, no socket,
//     no filesystem coupling with the Python daemon.
//
// Why SPM executable instead of an .xcodeproj:
// The monorepo is CLI-first; a hand-crafted Package.swift keeps the app
// reviewable in a diff and builds with `swift build` on any machine with the
// Xcode command-line tools. Opening `apps/gate-bar/Package.swift` in Xcode
// still gives the full GUI editor for anyone who wants one.
import PackageDescription

let package = Package(
    name: "GateBar",
    platforms: [
        .macOS(.v14),
    ],
    products: [
        // The app binary itself. Distribution (notarization, .app bundling,
        // Sparkle, Homebrew cask) is release-engineering scaffolding tracked
        // separately — not wired into the SPM manifest.
        .executable(name: "GateBar", targets: ["GateBar"]),
    ],
    targets: [
        .executableTarget(
            name: "GateBar",
            path: "Sources/GateBar"
        ),
        .testTarget(
            name: "GateBarTests",
            dependencies: ["GateBar"],
            path: "Tests/GateBarTests"
        ),
    ]
)
