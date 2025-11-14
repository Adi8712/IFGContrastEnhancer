from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog,
    QHBoxLayout, QVBoxLayout, QWidget, QStatusBar, QLabel,
    QDoubleSpinBox, QTabWidget
)
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QThread, Signal, QTimer
import sys
import os
import cv2

from src.clahe import apply as clahe_apply
from src.ifg import enhance as ifg_enhance

def resource_path(rel_path):
    base = sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.path.abspath(".")
    return os.path.join(base, rel_path)

class Worker(QThread):
    done = Signal(object, object, float)

    def __init__(self, img, clip):
        super().__init__()
        self.img = img
        self.clip = clip

    def run(self):
        bgr = self.img.copy()
        clahe_img = clahe_apply(bgr, clip=self.clip)
        ifg_img, k = ifg_enhance(bgr, clip=self.clip)
        self.done.emit(clahe_img, ifg_img, k)

class ImageView(QWidget):
    transformChanged = Signal(float, float, float)

    def __init__(self, label="Image", parent=None):
        super().__init__(parent)
        self.pix = None
        self.scale = 1.0
        self.offset_x = self.offset_y = 0.0
        self.last_pos = None
        self.label = label
        self.setMouseTracking(True)

    def set_image(self, img):
        if img is None:
            self.pix = None
            self.update()
            return
        h, w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, QImage.Format_RGB888)
        self.pix = QPixmap.fromImage(qimg)
        self.fit_to_view()

    def fit_to_view(self):
        if not self.pix or self.width() <= 0 or self.height() <= 0:
            return
        iw, ih = self.pix.width(), self.pix.height()
        self.scale = min(self.width() / iw, self.height() / ih)
        self.offset_x = (self.width() - iw * self.scale) / 2
        self.offset_y = (self.height() - ih * self.scale) / 2
        self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
        self.update()

    def clamp_offsets(self):
        if not self.pix:
            return
        iw, ih = self.pix.width(), self.pix.height()
        sw, sh = iw * self.scale, ih * self.scale
        vw, vh = self.width(), self.height()
        if sw <= vw:
            self.offset_x = (vw - sw) / 2
        else:
            self.offset_x = max(vw - sw, min(0, self.offset_x))
        if sh <= vh:
            self.offset_y = (vh - sh) / 2
        else:
            self.offset_y = max(vh - sh, min(0, self.offset_y))

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.clamp_offsets()
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(16, 18, 20))
        if not self.pix:
            return
        p.translate(self.offset_x, self.offset_y)
        p.scale(self.scale, self.scale)
        p.drawPixmap(0, 0, self.pix)
        p.resetTransform()
        p.setFont(QFont("Arial", 14, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(10, 30, self.label)

    def wheelEvent(self, ev):
        if not self.pix:
            return
        pos = ev.position()
        factor = 1.25 if ev.angleDelta().y() > 0 else 0.8
        old = self.scale
        iw, ih = self.pix.width(), self.pix.height()
        fit_scale = min(self.width() / iw, self.height() / ih)
        self.scale = max(fit_scale, min(50.0, old * factor))
        if self.scale == old:
            return
        mx = (pos.x() - self.offset_x) / old
        my = (pos.y() - self.offset_y) / old
        self.offset_x = pos.x() - mx * self.scale
        self.offset_y = pos.y() - my * self.scale
        self.clamp_offsets()
        self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() == Qt.LeftButton and self.pix:
            self.last_pos = ev.position()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        if self.last_pos and self.pix:
            d = ev.position() - self.last_pos
            self.offset_x += d.x()
            self.offset_y += d.y()
            self.last_pos = ev.position()
            self.clamp_offsets()
            self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
            self.update()
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        self.last_pos = None
        super().mouseReleaseEvent(ev)

    def set_transform(self, scale, ox, oy):
        self.scale, self.offset_x, self.offset_y = scale, ox, oy
        self.clamp_offsets()
        self.update()

class CompareView(QWidget):
    transformChanged = Signal(float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.left_pix = self.right_pix = None
        self.scale = 1.0
        self.offset_x = self.offset_y = 0.0
        self.divider_ratio = 0.5
        self.dragging = False
        self.last_pos = None
        self.left_label = "Original"
        self.right_label = "IFG"
        self.setMouseTracking(True)

    def set_images(self, left, right, left_label="Original", right_label="IFG"):
        self.left_label = left_label
        self.right_label = right_label
        if left is None or right is None:
            self.left_pix = self.right_pix = None
            self.update()
            return
        h, w = left.shape[:2]
        rgb1 = cv2.cvtColor(left, cv2.COLOR_BGR2RGB)
        q1 = QImage(rgb1.data, w, h, QImage.Format_RGB888)
        self.left_pix = QPixmap.fromImage(q1)
        rgb2 = cv2.cvtColor(right, cv2.COLOR_BGR2RGB)
        q2 = QImage(rgb2.data, w, h, QImage.Format_RGB888)
        self.right_pix = QPixmap.fromImage(q2)
        self.fit_to_view()

    def fit_to_view(self):
        if not self.left_pix or self.width() <= 0 or self.height() <= 0:
            return
        iw, ih = self.left_pix.width(), self.left_pix.height()
        self.scale = min(self.width() / iw, self.height() / ih)
        self.offset_x = (self.width() - iw * self.scale) / 2
        self.offset_y = (self.height() - ih * self.scale) / 2
        self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
        self.update()

    def clamp_offsets(self):
        if not self.left_pix:
            return
        iw, ih = self.left_pix.width(), self.left_pix.height()
        sw, sh = iw * self.scale, ih * self.scale
        vw, vh = self.width(), self.height()
        if sw <= vw:
            self.offset_x = (vw - sw) / 2
        else:
            self.offset_x = max(vw - sw, min(0, self.offset_x))
        if sh <= vh:
            self.offset_y = (vh - sh) / 2
        else:
            self.offset_y = max(vh - sh, min(0, self.offset_y))

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        self.clamp_offsets()
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        if self.left_pix and self.right_pix:
            QTimer.singleShot(0, self.fit_to_view)

    def paintEvent(self, ev):
        p = QPainter(self)
        p.fillRect(self.rect(), QColor(16, 18, 20))
        if not (self.left_pix and self.right_pix):
            return
        div = int(self.divider_ratio * self.width())
        p.save()
        p.setClipRect(0, 0, div, self.height())
        p.translate(self.offset_x, self.offset_y)
        p.scale(self.scale, self.scale)
        p.drawPixmap(0, 0, self.left_pix)
        p.restore()
        p.save()
        p.setClipRect(div, 0, self.width() - div, self.height())
        p.translate(self.offset_x, self.offset_y)
        p.scale(self.scale, self.scale)
        p.drawPixmap(0, 0, self.right_pix)
        p.restore()
        p.setPen(QPen(QColor("white"), 1))
        p.drawLine(div, 0, div, self.height())
        p.resetTransform()
        p.setFont(QFont("Arial", 14, QFont.Bold))
        p.setPen(QColor("white"))
        p.drawText(10, 30, self.left_label)
        p.drawText(self.width() - 80, 30, self.right_label)

    def wheelEvent(self, ev):
        if not self.left_pix:
            return
        pos = ev.position()
        factor = 1.25 if ev.angleDelta().y() > 0 else 0.8
        old = self.scale
        iw, ih = self.left_pix.width(), self.left_pix.height()
        fit_scale = min(self.width() / iw, self.height() / ih)
        self.scale = max(fit_scale, min(50.0, old * factor))
        if self.scale == old:
            return
        mx = (pos.x() - self.offset_x) / old
        my = (pos.y() - self.offset_y) / old
        self.offset_x = pos.x() - mx * self.scale
        self.offset_y = pos.y() - my * self.scale
        self.clamp_offsets()
        self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
        self.update()

    def mousePressEvent(self, ev):
        if ev.button() != Qt.LeftButton or not self.left_pix:
            return
        x = ev.position().x()
        div = self.divider_ratio * self.width()
        if abs(x - div) <= 10:
            self.dragging = True
        else:
            self.last_pos = ev.position()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev):
        pos = ev.position()
        if self.dragging:
            self.divider_ratio = max(0.05, min(0.95, pos.x() / self.width()))
            self.update()
        elif self.last_pos:
            d = pos - self.last_pos
            self.offset_x += d.x()
            self.offset_y += d.y()
            self.last_pos = pos
            self.clamp_offsets()
            self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
            self.update()
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev):
        self.dragging = False
        self.last_pos = None
        super().mouseReleaseEvent(ev)

    def set_transform(self, scale, ox, oy):
        self.scale, self.offset_x, self.offset_y = scale, ox, oy
        self.clamp_offsets()
        self.update()

class CentralWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, ev):
        ev.accept() if ev.mimeData().hasUrls() else ev.ignore()

    def dropEvent(self, ev):
        path = ev.mimeData().urls()[0].toLocalFile()
        if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            self.parent().load_from_path(path)

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

        self.orig = self.ifg = self.clahe = None
        self.orig_path = None
        self.updating = False
        self.run_btn.setEnabled(False)
        self.save_ifg.setEnabled(False)
        self.compare_mode_original = True

        for v in (self.orig_view, self.ifg_view, self.compare_view):
            v.transformChanged.connect(self.sync_transform)

        self.setStyleSheet("""
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
        """)

    def load_from_path(self, path):
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

    def load_image(self):
        start = resource_path("samples") if os.path.isdir(resource_path("samples")) else os.path.expanduser("~")
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", start,
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff)")
        if path:
            self.load_from_path(path)

    def run_enhancement(self):
        if self.orig is None:
            self.status.showMessage("Load an image first")
            return
        cur_scale, cur_ox, cur_oy = self.orig_view.scale, self.orig_view.offset_x, self.orig_view.offset_y
        self.run_btn.setEnabled(False)
        self.status.showMessage("Processing...")
        clip = self.clip_spin.value()
        self.worker = Worker(self.orig, clip)
        self.worker.done.connect(lambda c, i, k: self.on_done(c, i, k, cur_scale, cur_ox, cur_oy))
        self.worker.start()

    def on_done(self, clahe_img, ifg_img, k, saved_scale, saved_ox, saved_oy):
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

    def on_tab_changed(self, index):
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

    def toggle_compare_mode(self):
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

    def sync_transform(self, scale, ox, oy):
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

    def fit_all(self):
        cur = self.tabs.currentWidget()
        if isinstance(cur, ImageView) or isinstance(cur, CompareView):
            cur.fit_to_view()

    def save_image(self, kind):
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

def main(argv=None):
    app = QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("IFG-based Contrast Enhancement")
    win = MainWindow()
    win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
