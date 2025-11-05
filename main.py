from PySide6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QFileDialog,
    QHBoxLayout, QVBoxLayout, QWidget, QStatusBar
)
from PySide6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QFont
from PySide6.QtCore import Qt, QThread, Signal
import sys
import os
import cv2

from src.clahe import apply as clahe_apply
from src.ifg import enhance as ifg_enhance

def resource_path(rel_path):
    if hasattr(sys, "_MEIPASS"):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, rel_path)


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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pix = None
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.last_pos = None
        self.setMouseTracking(True)

    def set_image(self, img):
        h, w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, QImage.Format_RGB888)
        self.pix = QPixmap.fromImage(qimg)
        self.fit_to_view()
        self.update()

    def fit_to_view(self):
        if not self.pix or self.width() <= 0 or self.height() <= 0:
            return
        img_w, img_h = self.pix.width(), self.pix.height()
        scale_w = self.width() / img_w
        scale_h = self.height() / img_h
        self.scale = min(scale_w, scale_h)
        self.offset_x = (self.width() - img_w * self.scale) / 2
        self.offset_y = (self.height() - img_h * self.scale) / 2
        self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)

    def clamp_offsets(self):
        if not self.pix:
            return
        img_w, img_h = self.pix.width(), self.pix.height()
        scaled_w = img_w * self.scale
        scaled_h = img_h * self.scale
        view_w, view_h = self.width(), self.height()

        # X clamp
        if scaled_w <= view_w:
            self.offset_x = (view_w - scaled_w) / 2
        else:
            self.offset_x = max(view_w - scaled_w, min(0, self.offset_x))

        # Y clamp
        if scaled_h <= view_h:
            self.offset_y = (view_h - scaled_h) / 2
        else:
            self.offset_y = max(view_h - scaled_h, min(0, self.offset_y))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.clamp_offsets()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(16, 18, 20))
        if not self.pix:
            return
        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.scale, self.scale)
        painter.drawPixmap(0, 0, self.pix)

        # Draw label
        painter.resetTransform()
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.setPen(QColor("white"))
        painter.drawText(10, 30, "Original")

    def wheelEvent(self, event):
        if not self.pix:
            return
        pos = event.position()
        zoom_in = event.angleDelta().y() > 0
        factor = 1.25 if zoom_in else 0.8
        old_scale = self.scale
        intended_scale = old_scale * factor
        img_w, img_h = self.pix.width(), self.pix.height()
        fit_scale = min(self.width() / img_w, self.height() / img_h)
        self.scale = max(fit_scale, min(50.0, intended_scale))

        if self.scale == fit_scale:
            self.offset_x = (self.width() - img_w * self.scale) / 2
            self.offset_y = (self.height() - img_h * self.scale) / 2
        else:
            mx = (pos.x() - self.offset_x) / old_scale
            my = (pos.y() - self.offset_y) / old_scale
            self.offset_x = pos.x() - mx * self.scale
            self.offset_y = pos.y() - my * self.scale

        self.clamp_offsets()
        self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.pix:
            self.last_pos = event.position()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self.last_pos and self.pix:
            delta = event.position() - self.last_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_pos = event.position()
            self.clamp_offsets()
            self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.last_pos = None
        super().mouseReleaseEvent(event)

    def set_transform(self, scale, ox, oy):
        self.scale = scale
        self.offset_x = ox
        self.offset_y = oy
        self.clamp_offsets()
        self.update()


class CompareView(QWidget):
    transformChanged = Signal(float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.left_pix = self.right_pix = None
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.divider_ratio = 0.5
        self.dragging = False
        self.last_pos = None
        self.setMouseTracking(True)

    def set_images(self, left_img, right_img):
        h, w = left_img.shape[:2]
        rgb1 = cv2.cvtColor(left_img, cv2.COLOR_BGR2RGB)
        q1 = QImage(rgb1.data, w, h, QImage.Format_RGB888)
        self.left_pix = QPixmap.fromImage(q1)

        rgb2 = cv2.cvtColor(right_img, cv2.COLOR_BGR2RGB)
        q2 = QImage(rgb2.data, w, h, QImage.Format_RGB888)
        self.right_pix = QPixmap.fromImage(q2)

        self.fit_to_view()
        self.update()

    def fit_to_view(self):
        if not self.left_pix or self.width() <= 0 or self.height() <= 0:
            return
        img_w = self.left_pix.width()
        img_h = self.left_pix.height()
        scale_w = self.width() / img_w
        scale_h = self.height() / img_h
        self.scale = min(scale_w, scale_h)
        self.offset_x = (self.width() - img_w * self.scale) / 2
        self.offset_y = (self.height() - img_h * self.scale) / 2
        self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)

    def clamp_offsets(self):
        if not self.left_pix:
            return
        img_w, img_h = self.left_pix.width(), self.left_pix.height()
        scaled_w = img_w * self.scale
        scaled_h = img_h * self.scale
        view_w, view_h = self.width(), self.height()

        # X clamp
        if scaled_w <= view_w:
            self.offset_x = (view_w - scaled_w) / 2
        else:
            self.offset_x = max(view_w - scaled_w, min(0, self.offset_x))

        # Y clamp
        if scaled_h <= view_h:
            self.offset_y = (view_h - scaled_h) / 2
        else:
            self.offset_y = max(view_h - scaled_h, min(0, self.offset_y))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.clamp_offsets()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(16, 18, 20))
        if not self.left_pix or not self.right_pix:
            return

        divider_x = int(self.divider_ratio * self.width())

        # Left image
        painter.save()
        painter.setClipRect(0, 0, divider_x, self.height())
        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.scale, self.scale)
        painter.drawPixmap(0, 0, self.left_pix)
        painter.restore()

        # Right image
        painter.save()
        painter.setClipRect(divider_x, 0, self.width() - divider_x, self.height())
        painter.translate(self.offset_x, self.offset_y)
        painter.scale(self.scale, self.scale)
        painter.drawPixmap(0, 0, self.right_pix)
        painter.restore()

        # Divider line
        pen = QPen(QColor("white"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.drawLine(divider_x, 0, divider_x, self.height())

        # Draw labels
        painter.resetTransform()
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.setPen(QColor("white"))
        painter.drawText(10, 30, "CLAHE")
        painter.drawText(self.width() - 80, 30, "IFG")

    def wheelEvent(self, event):
        if not self.left_pix:
            return
        pos = event.position()
        zoom_in = event.angleDelta().y() > 0
        factor = 1.25 if zoom_in else 0.8
        old_scale = self.scale
        intended_scale = old_scale * factor
        img_w, img_h = self.left_pix.width(), self.left_pix.height()
        fit_scale = min(self.width() / img_w, self.height() / img_h)
        self.scale = max(fit_scale, min(50.0, intended_scale))

        if self.scale == fit_scale:
            self.offset_x = (self.width() - img_w * self.scale) / 2
            self.offset_y = (self.height() - img_h * self.scale) / 2
        else:
            mx = (pos.x() - self.offset_x) / old_scale
            my = (pos.y() - self.offset_y) / old_scale
            self.offset_x = pos.x() - mx * self.scale
            self.offset_y = pos.y() - my * self.scale

        self.clamp_offsets()
        self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
        self.update()

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton or not self.left_pix:
            return
        x = event.position().x()
        divider_x = self.divider_ratio * self.width()
        if abs(x - divider_x) <= 10:
            self.dragging = True
        else:
            self.last_pos = event.position()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        pos = event.position()
        if self.dragging:
            self.divider_ratio = max(0.05, min(0.95, pos.x() / self.width()))
            self.update()
        elif self.last_pos:
            delta = pos - self.last_pos
            self.offset_x += delta.x()
            self.offset_y += delta.y()
            self.last_pos = pos
            self.clamp_offsets()
            self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
            self.update()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.last_pos = None
        super().mouseReleaseEvent(event)

    def set_transform(self, scale, ox, oy):
        self.scale = scale
        self.offset_x = ox
        self.offset_y = oy
        self.clamp_offsets()
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IFG-based Contrast Enhancement")
        self.resize(1400, 800)

        central = QWidget()
        self.setCentralWidget(central)

        # Views
        self.orig_view = ImageView()
        self.compare_view = CompareView()

        for view in (self.orig_view, self.compare_view):
            view.setMinimumSize(400, 400)
            view.setStyleSheet("background: #101214; border-radius: 8px;")

        # Buttons
        load_btn = QPushButton("Load Image")
        run_btn = QPushButton("Run Enhancement")
        save_clahe = QPushButton("Save CLAHE")
        save_ifg = QPushButton("Save IFG")

        load_btn.clicked.connect(self.load_image)
        run_btn.clicked.connect(self.run_enhancement)
        save_clahe.clicked.connect(lambda: self.save_image("clahe"))
        save_ifg.clicked.connect(lambda: self.save_image("ifg"))

        # Layout
        top_layout = QHBoxLayout()
        for btn in (load_btn, run_btn, save_clahe, save_ifg):
            top_layout.addWidget(btn)

        views_layout = QHBoxLayout()
        views_layout.addWidget(self.orig_view, 1)
        views_layout.addWidget(self.compare_view, 1)

        main_layout = QVBoxLayout(central)
        main_layout.addLayout(top_layout)
        main_layout.addLayout(views_layout, 1)

        # Status bar
        self.status = QStatusBar()
        self.setStatusBar(self.status)

        # State
        self.orig = self.clahe = self.ifg = None
        self.clip = 2.0
        self.updating = False

        # Sync transform
        self.orig_view.transformChanged.connect(self.sync_transform)
        self.compare_view.transformChanged.connect(self.sync_transform)

        # Style
        self.setStyleSheet("""
            QMainWindow { background: #0b0c0d; color: #dbe2ef; }
            QStatusBar { 
                background: #0b0c0d; /* Status bar background color */
                color: white; /* Fallback text color for status bar */
            }
            QStatusBar QLabel { 
                color: white; /* Ensures the showMessage text is white */
            }
            QPushButton {
                background: #121317; color: #e6eef8; padding: 8px 16px;
                border-radius: 6px; border: none;
            }
            QPushButton:hover { background: #1e2127; }
            QPushButton:pressed { background: #2a2d35; }
        """)

    def load_image(self):
        samples_dir = resource_path("samples")
        if not os.path.exists(samples_dir):
            samples_dir = os.path.expanduser("~")


        path, _ = QFileDialog.getOpenFileName(
            self, "Open Image", samples_dir,
            "Images (*.png *.jpg *.jpeg *.bmp *.tiff)"
        )
        if not path or not os.path.exists(path):
            return
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            self.status.showMessage("Failed to load image")
            return
        self.orig = img
        self.clahe = self.ifg = None
        self.orig_view.set_image(img)
        self.status.showMessage(f"Loaded: {os.path.basename(path)}")

    def run_enhancement(self):
        if self.orig is None:
            self.status.showMessage("Load an image first")
            return
        self.status.showMessage("Processing...")
        self.worker = Worker(self.orig, self.clip)
        self.worker.done.connect(self.on_done)
        self.worker.start()

    def on_done(self, clahe_img, ifg_img, k):
        self.clahe, self.ifg = clahe_img, ifg_img
        self.compare_view.set_images(clahe_img, ifg_img)
        self.status.showMessage(f"k = {k:.3f}")

    def sync_transform(self, scale, ox, oy):
        if self.updating:
            return
        self.updating = True
        sender = self.sender()
        if sender is self.orig_view:
            self.compare_view.set_transform(scale, ox, oy)
        else:
            self.orig_view.set_transform(scale, ox, oy)
        self.updating = False

    def save_image(self, kind):
        img = self.clahe if kind == "clahe" else self.ifg
        if img is None:
            return
        name = "CLAHE" if kind == "clahe" else "IFG"
        path, _ = QFileDialog.getSaveFileName(
            self, f"Save {name}", "", "PNG (*.png);;JPEG (*.jpg)"
        )
        if path:
            cv2.imwrite(path, img)
            self.status.showMessage(f"Saved {name}")


def main(argv=None):
    app = QApplication(sys.argv if argv is None else argv)
    app.setApplicationName("IFG-based Contrast Enhancement")
    win = MainWindow()
    win.show()
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
