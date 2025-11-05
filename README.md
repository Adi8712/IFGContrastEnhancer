# IFG-Based Contrast Enhancement

**A standalone, cross-platform application for low-contrast color image enhancement using the Intuitionistic Fuzzy Generator (IFG) approach.**

---

## Overview

This application provides an easy-to-use interface for enhancing low-contrast images using the **Intuitionistic Fuzzy Generator (IFG)**–based algorithm introduced by **Selvam et al., 2024 (Information Fusion)**.

It fuses the novel IFG method with **Contrast Limited Adaptive Histogram Equalization (CLAHE)** to improve visibility and contrast in dark or low-illumination images.
The project wraps this method in a **Qt-based GUI** for visual comparison.

---

## Installation

### From Source

Clone this repository and install dependencies:

```bash
git clone https://github.com/yourusername/ifg-based-contrast-enhancement.git
cd ifg-based-contrast-enhancement
python -m venv .venv
source .venv/bin/activate
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

   * The file dialog starts in the bundled `samples/` folder.
   * Supported formats: `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`.

3. **Run Enhancement**

   * Click **Run Enhancement** to process the image using both CLAHE and IFG methods.
   * The right pane shows the IFG-enhanced output, the left pane shows CLAHE.

4. **Compare & Export**

   * Drag the divider line to compare the results interactively.
   * Save either output using **Save CLAHE** or **Save IFG**.

---

## Project Structure

```
.
├── main.py
├── src/
│   ├── __init__.py
│   ├── clahe.py
│   └── ifg.py
├── samples/
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Dependencies

Core dependencies (see `requirements.txt`):

* **Python ≥ 3.13**
* `PySide6` — GUI framework
* `opencv-python` — Image processing
* `numpy` — Matrix and numerical operations
* `matplotlib` — Optional plotting utilities

Install all with:

```bash
pip install -r requirements.txt
```

---

## Packaging (Optional)

To build a standalone binary:

```bash
pyinstaller --onefile --name IFGContrastEnhancer --add-data "samples:samples" main.py
```

This creates a single executable inside `dist/`.

---

## Credits and Acknowledgments

This software is an open implementation of the image enhancement algorithm described in:

> **Selvam, C., Jebadass, R.J.J., Sundaram, D., & Shanmugam, L.**
> *A novel intuitionistic fuzzy generator for low-contrast color image enhancement technique.*
> *Information Fusion, 108 (2024), 102365.*
> [https://doi.org/10.1016/j.inffus.2024.102365](https://doi.org/10.1016/j.inffus.2024.102365)

Algorithmic references and mathematical formulations belong to the original authors.
This application serves as an educational and practical tool for demonstrating their work.

Developed and adapted for general-purpose use by me.

---

## License

This project is released under the **MIT License**.
You are free to use, modify, and distribute the code, provided appropriate credit is given.

---
