"""Application entrypoint"""

import sys
from PySide6.QtWidgets import QApplication
from src.gui.window import MainWindow


def main(argv=None):
    app = QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("IFG-based Contrast Enhancement")
    win = MainWindow()
    win.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
