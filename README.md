# IFG-Based Contrast Enhancement

**A standalone, cross-platform application for low-contrast color image enhancement using the Intuitionistic Fuzzy Generator (IFG) approach.**

---

## Overview

This application provides an easy-to-use interface for enhancing low-contrast images using the **Intuitionistic Fuzzy Generator (IFG)**–based algorithm introduced by **Selvam et al., 2024 (Information Fusion)**.

It combines the novel IFG method with **Contrast Limited Adaptive Histogram Equalization (CLAHE)** to improve visibility and contrast in dark or low-illumination images.
The project wraps this method in a **Qt-based GUI** for side-by-side visual comparison.

---

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

Run the app:

```bash
python main.py
```

### From Executable

If you built it with PyInstaller:

```bash
./dist/IFGContrastEnhancer
```

---

## Usage

1. **Open the application**
   Launch `IFGContrastEnhancer` or run `python main.py`.

2. **Load an image**

   * The file dialog opens inside the bundled `samples/` folder by default.
   * Supported formats: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`.

3. **Run Enhancement**

   * Click **Run Enhancement** to process the image using both CLAHE and IFG methods.
   * The **left pane** shows the CLAHE-enhanced image.
   * The **right pane** shows the IFG-enhanced result.

4. **Compare & Export**

   * Drag the divider line to compare the two results interactively.
   * Use **Save CLAHE** or **Save IFG** to export individual outputs.

---

## Project Structure

```
.
├── main.py                  # GUI and application entrypoint
├── src/
│   ├── __init__.py
│   ├── clahe.py             # CLAHE enhancement module
│   └── ifg.py               # IFG-based enhancement algorithm
├── samples/                 # Sample images for testing
├── pyproject.toml           # Project configuration
├── requirements.txt         # Dependency list
└── README.md
```

---

## Dependencies

Core dependencies (see `requirements.txt`):

* **Python ≥ 3.13**
* `PySide6` — Qt-based GUI framework
* `opencv-python` — Image processing
* `numpy` — Numerical computation
* `matplotlib` — Optional plotting utilities

Install all dependencies with:

```bash
pip install -r requirements.txt
```

---

## Packaging (Optional)

To build a standalone executable (using PyInstaller):

```bash
pyinstaller --onefile --name IFGContrastEnhancer --add-data "samples:samples" main.py
```

This will generate a single packaged binary inside the `dist/` folder.

---

## Samples

Sample images used for testing and demonstration were sourced from:
[Google Drive – LOw Light paired dataset (LOL)](https://drive.google.com/open?id=157bjO1_cFuSd0HWDUuAmcHRJDVyWpOxB)

These images are provided for educational and evaluation purposes.

---

## Credits and Acknowledgments

This application is an open-source implementation of the image enhancement algorithm described in:

> **Selvam, C., Jebadass, R.J.J., Sundaram, D., & Shanmugam, L.**
> *A novel intuitionistic fuzzy generator for low-contrast color image enhancement technique.*
> *Information Fusion, 108 (2024), 102365.*
> [https://doi.org/10.1016/j.inffus.2024.102365](https://doi.org/10.1016/j.inffus.2024.102365)

All mathematical formulations and algorithmic contributions belong to the original authors.
This project provides an accessible, visual implementation for educational, research, and demonstration use.

Developed and adapted for general-purpose use by **me**.

---

## License

This project is distributed under the **MIT License**.
You are free to use, modify, and distribute the software, provided proper credit is given to the original authors and contributors.

---
