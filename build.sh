#!/usr/bin/env bash
set -euo pipefail

# Cross-platform build helper for PyInstaller
# Usage: ./build.sh
# - Bundles ./samples into the executable if the folder exists.
# - Produces a single-file build in ./dist/
# Notes:
# - Run this script with a Python environment where pyinstaller is installed.
# - On Windows run from Git Bash / MSYS2 / WSL or adapt to a PowerShell script.

APP_NAME="IFGContrastEnhancer"
ENTRY="main.py"
DIST_DIR="./dist"
BUILD_DIR="./build"
SPEC_FILE="${APP_NAME}.spec"

OS_UNAME="$(uname -s || echo Unknown)"

is_windows() {
    case "${OS_UNAME}" in
        CYGWIN*|MINGW32*|MSYS*|MINGW*) return 0 ;;
        *) return 1 ;;
    esac
}

is_mac() {
    [[ "${OS_UNAME}" == "Darwin" ]]
}

is_linux() {
    [[ "${OS_UNAME}" == "Linux" ]]
}

pyinstaller_common_flags=(--onefile --name "${APP_NAME}" --distpath "${DIST_DIR}" --workpath "${BUILD_DIR}" --optimize 2 --clean --windowed)
pyinstaller_unix_flags=(--strip)

rm -rf "${DIST_DIR}" "${BUILD_DIR}" "${SPEC_FILE}"

echo "Detected platform: ${OS_UNAME}"

cmd=(pyinstaller "${pyinstaller_common_flags[@]}")
if ! is_windows; then
    cmd+=("${pyinstaller_unix_flags[@]}")
fi
if [ -d "samples" ]; then
    echo "Including samples/ in bundle"
    if is_windows; then
        cmd+=("--add-data" "samples;samples")
    else
        cmd+=("--add-data" "samples:samples")
    fi
fi
cmd+=("${ENTRY}")

if is_windows; then
    "${cmd[@]}" > /dev/null 2> /dev/null || {
        echo "Error: PyInstaller build failed"
        exit 1
    }
else
    if ! "${cmd[@]}" > /dev/null 2>&1; then
        echo "Error: PyInstaller build failed"
        exit 1
    fi
fi

if is_windows; then
    EXE_PATH="${DIST_DIR}/${APP_NAME}.exe"
else
    EXE_PATH="${DIST_DIR}/${APP_NAME}"
    if [ -f "${EXE_PATH}" ]; then
        chmod +x "${EXE_PATH}" || true
    fi
fi

if [ -f "${EXE_PATH}" ]; then
    echo "Build succeeded"
    echo "Executable: ${EXE_PATH}"
    exit 0
else
    echo "Build produced no executable"
    exit 2
fi
