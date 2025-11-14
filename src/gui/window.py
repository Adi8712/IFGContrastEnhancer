"""MainWindow implementation for the IFG Contrast Enhancer"""

from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QPushButton, QFileDialog, QHBoxLayout, QVBoxLayout,
    QStatusBar, QLabel, QDoubleSpinBox, QTabWidget
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, QTimer

import os
import cv2
import numpy as np

from src.gui.imageView import ImageView, CompareView, CentralWidget
from src.gui.worker import Worker
from src.utils.resource import resource_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IFG-based Contrast Enhancement")
        self.resize(1450, 850)

        central = CentralWidget(self)
        self.setCentralWidget(central)

        self.orig_view = ImageView("Original")
        self.ifg_view = ImageView("IFG")
        self.compare_view = CompareView()

        for v in (self.orig_view, self.ifg_view, self.compare_view):
            v.setMinimumSize(400, 400)
            v.setStyleSheet("background:#101214;border-radius:8px;")

        self.tabs = QTabWidget()
        self.tabs.addTab(self.orig_view, "Original")
        self.tabs.addTab(self.ifg_view, "IFG")
        self.tabs.addTab(self.compare_view, "Compare")
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        self.load_btn = QPushButton("Load Image")
        self.run_btn = QPushButton("Run Enhancement")
        self.save_ifg = QPushButton("Save IFG")
        self.fit_btn = QPushButton("Fit to View")

        self.load_btn.setToolTip("Load an image file")
        self.run_btn.setToolTip("Apply enhancement with current clip limit")
        self.save_ifg.setToolTip("Save the enhanced IFG image")
        self.fit_btn.setToolTip("Fit the image to the view")

        self.load_btn.clicked.connect(self.load_image)
        self.run_btn.clicked.connect(self.run_enhancement)
        self.save_ifg.clicked.connect(lambda: self.save_image("ifg"))
        self.fit_btn.clicked.connect(self.fit_all)

        clip_lbl = QLabel("Clip limit:")
        clip_lbl.setToolTip("Adjust the clip limit for enhancement")
        self.clip_spin = QDoubleSpinBox()
        self.clip_spin.setRange(0.1, 10.0)
        self.clip_spin.setSingleStep(0.1)
        self.clip_spin.setValue(2.0)
        self.clip_spin.setDecimals(2)
        self.clip_spin.setFixedWidth(100)
        self.clip_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)

        self.toggle_compare_btn = QPushButton("Original vs IFG")
        self.toggle_compare_btn.setCheckable(True)
        self.toggle_compare_btn.setToolTip("Toggle between Original vs IFG and CLAHE vs IFG")
        self.toggle_compare_btn.clicked.connect(self.toggle_compare_mode)
        self.toggle_compare_btn.setEnabled(False)

        top = QHBoxLayout()
        top.addWidget(self.load_btn)
        top.addWidget(self.run_btn)
        top.addWidget(clip_lbl)
        top.addWidget(self.clip_spin)
        top.addStretch()
        top.addWidget(self.toggle_compare_btn)
        top.addWidget(self.fit_btn)
        top.addWidget(self.save_ifg)

        main = QVBoxLayout(central)
        main.addLayout(top)
        main.addWidget(self.tabs, 1)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status_timer = QTimer(self)
        self.status_timer.setSingleShot(True)
        self.status_timer.timeout.connect(self.status.clearMessage)

        self.orig: Optional[np.ndarray] = None
        self.ifg: Optional[np.ndarray] = None
        self.clahe: Optional[np.ndarray] = None
        self.orig_path: Optional[str] = None
        self.updating = False
        self.run_btn.setEnabled(False)
        self.save_ifg.setEnabled(False)
        self.compare_mode_original = True

        for v in (self.orig_view, self.ifg_view, self.compare_view):
            v.transformChanged.connect(self.sync_transform)

        self.setStyleSheet(self._style())

    def _style(self) -> str:
        return """
            QMainWindow {background: #0b0c0d; color: #dbe2ef;}
            QStatusBar {background: #0b0c0d; color: white; font-size: 12px;}
            QPushButton {
                background: #121317; color: #e6eef8; padding: 8px 16px;
                border-radius: 6px; border: none; font-weight: 500;
            }
            QPushButton:hover {background: #1e2127;}
            QPushButton:pressed {background: #2a2d35;}
            QPushButton:disabled {background: #121317; color: #5a5a5a;}
            QPushButton:checked {background: #2a2d35; color: #ffffff;}
            QTabWidget::pane {border: none; background: #0b0c0d;}
            QTabBar::tab {
                background: #121317; color: #e6eef8; padding: 10px 20px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
                margin-right: 2px; font-weight: 500;
            }
            QTabBar::tab:selected {background: #2a2d35;}
            QTabBar::tab:disabled {color: #5a5a5a;}
            QDoubleSpinBox {
                background: #121317; color: #e6eef8; padding: 6px 8px;
                border-radius: 6px; border: none; selection-background-color: #2a2d35;
                min-width: 70px;
            }
            QLabel {color: #dbe2ef; font-weight: 500;}
        """

    def load_from_path(self, path: str) -> None:
        if not path or not os.path.exists(path):
            return
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            self.status.showMessage("Failed to load image")
            return
        self.orig = img
        self.orig_path = path
        self.ifg = self.clahe = None
        self.orig_view.set_image(img)
        self.ifg_view.set_image(None)
        self.compare_view.set_images(None, None)
        self.tabs.setTabEnabled(1, False)
        self.tabs.setTabEnabled(2, False)
        self.run_btn.setEnabled(True)
        self.save_ifg.setEnabled(False)
        self.toggle_compare_btn.setEnabled(False)
        self.toggle_compare_btn.setChecked(False)
        self.toggle_compare_btn.setText("Original vs IFG")
        self.compare_mode_original = True
        self.status.showMessage(f"Loaded: {os.path.basename(path)}")
        self.status_timer.start(5000)

    def load_image(self) -> None:
        samples_dir = resource_path("samples")

        start_dir = samples_dir if os.path.isdir(samples_dir) else os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Image",
            start_dir,
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if path:
            self.load_from_path(path)

    def run_enhancement(self) -> None:
        if self.orig is None:
            self.status.showMessage("Load an image first")
            return
        cur_scale, cur_ox, cur_oy = self.orig_view.scale, self.orig_view.offset_x, self.orig_view.offset_y
        self.run_btn.setEnabled(False)
        self.status.showMessage("Processing")
        clip = self.clip_spin.value()
        self.worker = Worker(self.orig, clip)
        self.worker.done.connect(lambda c, i, k: self.on_done(c, i, k, cur_scale, cur_ox, cur_oy))
        self.worker.start()

    def on_done(self, clahe_img, ifg_img, k: float, saved_scale: float, saved_ox: float, saved_oy: float) -> None:
        self.clahe, self.ifg = clahe_img, ifg_img
        self.ifg_view.set_image(ifg_img)
        self.compare_mode_original = True
        self.toggle_compare_btn.setChecked(False)
        self.toggle_compare_btn.setText("Original vs IFG")
        self.compare_view.set_images(self.orig, self.ifg, "Original", "IFG")
        self.tabs.setTabEnabled(1, True)
        self.tabs.setTabEnabled(2, True)
        self.save_ifg.setEnabled(True)
        self.run_btn.setEnabled(True)

        for v in (self.orig_view, self.ifg_view):
            if v.pix is not None:
                v.set_transform(saved_scale, saved_ox, saved_oy)
        if self.compare_view.left_pix is not None:
            self.compare_view.set_transform(saved_scale, saved_ox, saved_oy)

        self.status.showMessage(f"Processed (k = {k:.3f})")
        self.status_timer.start(5000)

        if self.tabs.currentWidget() == self.compare_view:
            self.toggle_compare_btn.setEnabled(True)

    def on_tab_changed(self, index: int) -> None:
        current = self.tabs.widget(index)
        if current == self.compare_view:
            if self.ifg is not None:
                self.toggle_compare_btn.setEnabled(True)
                if self.compare_mode_original:
                    self.compare_view.set_images(self.orig, self.ifg, "Original", "IFG")
                else:
                    self.compare_view.set_images(self.clahe, self.ifg, "CLAHE", "IFG")
            else:
                self.toggle_compare_btn.setEnabled(False)
        else:
            self.toggle_compare_btn.setEnabled(False)

    def toggle_compare_mode(self) -> None:
        if not self.toggle_compare_btn.isEnabled():
            return
        if self.toggle_compare_btn.isChecked():
            if self.clahe is not None:
                self.compare_view.set_images(self.clahe, self.ifg, "CLAHE", "IFG")
                self.toggle_compare_btn.setText("CLAHE vs IFG")
                self.compare_mode_original = False
            else:
                self.toggle_compare_btn.setChecked(False)
        else:
            self.compare_view.set_images(self.orig, self.ifg, "Original", "IFG")
            self.toggle_compare_btn.setText("Original vs IFG")
            self.compare_mode_original = True

    def sync_transform(self, scale: float, ox: float, oy: float) -> None:
        if self.updating:
            return
        self.updating = True
        sender = self.sender()
        for v in (self.orig_view, self.ifg_view):
            if v != sender and v.pix is not None:
                v.set_transform(scale, ox, oy)
        if self.compare_view != sender and self.compare_view.left_pix is not None:
            self.compare_view.set_transform(scale, ox, oy)
        self.updating = False

    def fit_all(self) -> None:
        cur = self.tabs.currentWidget()
        if isinstance(cur, ImageView) or isinstance(cur, CompareView):
            cur.fit_to_view()

    def save_image(self, kind: str) -> None:
        img = self.ifg
        if img is None:
            return
        base = os.path.basename(self.orig_path).rsplit(".", 1)[0] if self.orig_path else "enhanced"
        suggest = f"{base}_ifg.png"
        dir_ = os.path.dirname(self.orig_path) if self.orig_path else ""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save IFG", os.path.join(dir_, suggest),
            "PNG (*.png);;JPEG (*.jpg)")
        if path:
            cv2.imwrite(path, img)
            self.status.showMessage("Saved IFG")
            self.status_timer.start(5000)
