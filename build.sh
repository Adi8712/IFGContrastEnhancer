#!/bin/bash

APP_NAME="IFGContrastEnhancer"

OS=$(uname -s)

build_command() {
    local os_name=$1

    local sample_data="samples:samples"
    if [[ "$os_name" == "Windows" ]]; then
        sample_data="samples;samples"
    fi

    local cmd="pyinstaller --onefile --name $APP_NAME --add-data $sample_data --optimize 2 --windowed --strip --clean --distpath ./dist --workpath \"./build\" main.py > /dev/null 2>&1"

    eval "$cmd"

    if [[ $? -ne 0 ]]; then
        echo "Error: Build failed for $APP_NAME."
        return 1
    fi

}

build_platform() {
    local platform=$1

    echo "Building for $platform..."
    build_command "$platform"
    if [[ $? -ne 0 ]]; then
        return 1
    fi

    case "$platform" in
        Linux)
            chmod +x ./dist/$APP_NAME
            echo "Build complete. Run the application ./dist/$APP_NAME"
            ;;
        macOS)
            chmod +x ./dist/$APP_NAME
            echo "Build complete. Run the application ./dist/$APP_NAME"
            ;;
        Windows)
            echo "Build complete. Run the application ./dist/$APP_NAME.exe"
            ;;
    esac
}

case "$OS" in
    Linux)
        build_platform "Linux"
        ;;
    Darwin)
        build_platform "macOS"
        ;;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)
        build_platform "Windows"
        ;;
    *)
        echo "Unsupported OS: $OS"
        exit 1
        ;;
esac
