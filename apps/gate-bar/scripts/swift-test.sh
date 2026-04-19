#!/usr/bin/env bash
#
# Thin wrapper around `swift test` that makes Swift Testing work on
# machines with only the Command Line Tools installed (no Xcode.app).
#
# Why this exists:
#   - Swift Testing (`import Testing`) is the framework our tests use.
#   - Its runtime deps — Testing.framework + lib_TestingInterop.dylib —
#     live in the Xcode toolchain but dyld only looks in a handful of
#     default paths. Xcode.app sets those up automatically; plain CLT
#     does not.
#   - The fix is to point the build at the right -F dir and add two
#     rpaths so the xctest bundle can dlopen the framework at runtime.
#
# On a machine with Xcode.app installed, `swift test` works directly —
# but running this script there is still safe (it just adds redundant
# rpaths, no harm done).
#
# Usage:
#   ./scripts/swift-test.sh            # default invocation
#   ./scripts/swift-test.sh --filter X # forwards any extra args

set -euo pipefail

# Pick the active developer directory. `xcode-select -p` returns the Xcode
# path if one is selected, otherwise the CLT path.
DEVDIR="$(xcode-select -p 2>/dev/null || echo /Library/Developer/CommandLineTools)"

# Xcode.app layout: <dev>/usr/lib/... + Frameworks under <dev>/../Frameworks
# CLT layout:       <dev>/Library/Developer/Frameworks + .../usr/lib
if [[ -d "$DEVDIR/Library/Developer/Frameworks" ]]; then
  FRAMEWORKS_DIR="$DEVDIR/Library/Developer/Frameworks"
  INTEROP_DIR="$DEVDIR/Library/Developer/usr/lib"
elif [[ -d "$DEVDIR/../SharedFrameworks" ]]; then
  # Xcode.app — Testing.framework ships in a different location; fall back
  # to letting swift test find it on its own.
  exec swift test "$@"
else
  FRAMEWORKS_DIR="$DEVDIR/Library/Developer/Frameworks"
  INTEROP_DIR="$DEVDIR/Library/Developer/usr/lib"
fi

cd "$(dirname "$0")/.."

exec swift test \
  -Xswiftc -F -Xswiftc "$FRAMEWORKS_DIR" \
  -Xlinker -rpath -Xlinker "$FRAMEWORKS_DIR" \
  -Xlinker -rpath -Xlinker "$INTEROP_DIR" \
  "$@"
