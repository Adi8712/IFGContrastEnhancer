# IFG-Based Contrast Enhancement

A standalone, cross-platform application for low-contrast color image enhancement using the Intuitionistic Fuzzy Generator (IFG) approach.

## Overview

This application enhances low-light and low-contrast images using a two-stage pipeline:

1. **Intuitionistic Fuzzy Generator (IFG)**  
   Transforms the luminance component of an image using fuzzy membership, non-membership, and hesitation principles, while optimizing the parameter *k* using entropy maximization.

2. **Contrast Limited Adaptive Histogram Equalization (CLAHE)**  
   Improves local contrast while suppressing noise.

The GUI provides:

- Interactive image loading (including drag-and-drop)
- CLAHE and IFG enhancement
- Side-by-side comparison (Original vs IFG, or CLAHE vs IFG)
- Zooming, panning, and divider-based comparison
- Exporting enhanced output images

## Installation

### From Source

Clone this repository and install dependencies:

```bash
git clone git@github.com:Adi8712/IFGContrastEnhancer.git
cd IFGContrastEnhancer
python -m venv .venv
source .venv/bin/activate       # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

### From Executable (PyInstaller Build)

If you built a standalone executable:

```bash
./dist/IFGContrastEnhancer        # Linux/macOS
dist/IFGContrastEnhancer.exe      # Windows
```

## Usage

1. **Launch the application**

   ```bash
   python main.py
   ```

   or run the packaged executable.

2. **Load an image**

   * Opens inside the project's `samples/` directory by default
   * Supported formats: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`
   * You may also drag-and-drop files onto the window

3. **Run Enhancement**

   * Click **Run Enhancement**
   * CLAHE and IFG-enhanced images will be generated
   * The optimized *k* value is shown in the status bar

4. **Compare results**

   * Use the "Compare" tab for side-by-side comparison
   * Switch between "Original vs IFG" and "CLAHE vs IFG"
   * Drag the divider for interactive region comparison

5. **Save output**

   * Export the IFG-enhanced result as PNG or JPEG

## Project Structure

```
.
├── build.sh                      # Cross-platform PyInstaller build helper
├── main.py                       # Application entrypoint
├── pyproject.toml                # Project metadata and dependencies
├── requirements.txt              # Pinned package versions
├── samples/                      # Optional sample input images
└── src/
    ├── enhancements/
    │   ├── clahe.py              # CLAHE enhancement implementation
    │   └── ifg.py                # IFG enhancement algorithm
    ├── gui/
    │   ├── image_views.py        # Image display and comparison widgets
    │   ├── worker.py             # Background processing thread
    │   └── main_window.py        # Main GUI layout and actions
    └── utils/
        └── resource.py           # PyInstaller-safe resource path handling
```

## Dependencies

The application relies on:

* Python
* PySide6
* OpenCV (opencv-python)
* NumPy

Install all dependencies with:

```bash
pip install -r requirements.txt
```

## Building a Standalone Executable

The project includes a **platform-independent `build.sh`** script that works on:

* Linux
* macOS
* Windows (via Git Bash, MSYS2, or WSL)

It automatically:

* Cleans old build artifacts
* Packages the app using PyInstaller
* Bundles the `samples/` directory if present

### Run the build

```bash
chmod +x build.sh
./build.sh
```

The final executable will appear in:

```
dist/IFGContrastEnhancer      # Linux/macOS
dist/IFGContrastEnhancer.exe  # Windows
```

## Samples

The `samples/` directory contains optional demo images.
When using the packaged executable, these images are bundled automatically (if present during build).

[Google Drive – LOw Light paired dataset (LOL)](https://drive.google.com/open?id=157bjO1_cFuSd0HWDUuAmcHRJDVyWpOxB)

These images are provided for educational and evaluation purposes.

## Credits and Acknowledgments

This application is an open-source implementation of the image enhancement algorithm described in:

> **Selvam, C., Jebadass, R.J.J., Sundaram, D., & Shanmugam, L.**
> *A novel intuitionistic fuzzy generator for low-contrast color image enhancement technique.*
> *Information Fusion, 108 (2024), 102365.*
> [https://doi.org/10.1016/j.inffus.2024.102365](https://doi.org/10.1016/j.inffus.2024.102365)

All mathematical formulations and algorithmic contributions belong to the original authors.
This project provides an accessible, visual implementation for educational, research, and demonstration use.

Developed and adapted for general-purpose use by **me**.

## License

This project is distributed under the **MIT License**.
You are free to use, modify, and distribute the software, provided proper credit is given to the original authors and contributors.
