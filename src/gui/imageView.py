"""Reusable image view widgets used by the MainWindow"""

from typing import Optional, Tuple
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPixmap, QImage, QPainter, QFont, QColor, QPen
from PySide6.QtCore import Qt, QTimer, Signal
import cv2
import numpy as np


class ImageView(QWidget):
    transformChanged = Signal(float, float, float)

    def __init__(self, label: str = "Image", parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.pix: Optional[QPixmap] = None
        self.scale: float = 1.0
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self.last_pos = None
        self.label = label
        self.setMouseTracking(True)

    def set_image(self, img: Optional[np.ndarray]) -> None:
        if img is None:
            self.pix = None
            self.update()
            return
        h, w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        qimg = QImage(rgb.data, w, h, QImage.Format_RGB888)
        self.pix = QPixmap.fromImage(qimg)
        self.fit_to_view()

    def fit_to_view(self) -> None:
        if not self.pix or self.width() <= 0 or self.height() <= 0:
            return
        iw, ih = self.pix.width(), self.pix.height()
        self.scale = min(self.width() / iw, self.height() / ih)
        self.offset_x = (self.width() - iw * self.scale) / 2
        self.offset_y = (self.height() - ih * self.scale) / 2
        self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
        self.update()

    def clamp_offsets(self) -> None:
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

    def resizeEvent(self, ev) -> None:
        super().resizeEvent(ev)
        self.clamp_offsets()
        self.update()

    def paintEvent(self, ev) -> None:
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

    def wheelEvent(self, ev) -> None:
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

    def mousePressEvent(self, ev) -> None:
        if ev.button() == Qt.LeftButton and self.pix:
            self.last_pos = ev.position()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev) -> None:
        if self.last_pos and self.pix:
            d = ev.position() - self.last_pos
            self.offset_x += d.x()
            self.offset_y += d.y()
            self.last_pos = ev.position()
            self.clamp_offsets()
            self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
            self.update()
        super().mouseMoveEvent(ev)

    def mouseReleaseEvent(self, ev) -> None:
        self.last_pos = None
        super().mouseReleaseEvent(ev)

    def set_transform(self, scale: float, ox: float, oy: float) -> None:
        self.scale, self.offset_x, self.offset_y = scale, ox, oy
        self.clamp_offsets()
        self.update()


class CompareView(QWidget):
    transformChanged = Signal(float, float, float)

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.left_pix: Optional[QPixmap] = None
        self.right_pix: Optional[QPixmap] = None
        self.scale: float = 1.0
        self.offset_x: float = 0.0
        self.offset_y: float = 0.0
        self.divider_ratio: float = 0.5
        self.dragging = False
        self.last_pos = None
        self.left_label = "Original"
        self.right_label = "IFG"
        self.setMouseTracking(True)

    def set_images(self, left: Optional[np.ndarray], right: Optional[np.ndarray],
                   left_label: str = "Original", right_label: str = "IFG") -> None:
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

    def fit_to_view(self) -> None:
        if not self.left_pix or self.width() <= 0 or self.height() <= 0:
            return
        iw, ih = self.left_pix.width(), self.left_pix.height()
        self.scale = min(self.width() / iw, self.height() / ih)
        self.offset_x = (self.width() - iw * self.scale) / 2
        self.offset_y = (self.height() - ih * self.scale) / 2
        self.transformChanged.emit(self.scale, self.offset_x, self.offset_y)
        self.update()

    def clamp_offsets(self) -> None:
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

    def resizeEvent(self, ev) -> None:
        super().resizeEvent(ev)
        self.clamp_offsets()
        self.update()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self.left_pix and self.right_pix:
            QTimer.singleShot(0, self.fit_to_view)

    def paintEvent(self, ev) -> None:
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

    def wheelEvent(self, ev) -> None:
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

    def mousePressEvent(self, ev) -> None:
        if ev.button() != Qt.LeftButton or not self.left_pix:
            return
        x = ev.position().x()
        div = self.divider_ratio * self.width()
        if abs(x - div) <= 10:
            self.dragging = True
        else:
            self.last_pos = ev.position()
        super().mousePressEvent(ev)

    def mouseMoveEvent(self, ev) -> None:
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

    def mouseReleaseEvent(self, ev) -> None:
        self.dragging = False
        self.last_pos = None
        super().mouseReleaseEvent(ev)

    def set_transform(self, scale: float, ox: float, oy: float) -> None:
        self.scale, self.offset_x, self.offset_y = scale, ox, oy
        self.clamp_offsets()
        self.update()


class CentralWidget(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, ev) -> None:
        ev.accept() if ev.mimeData().hasUrls() else ev.ignore()

    def dropEvent(self, ev) -> None:
        path = ev.mimeData().urls()[0].toLocalFile()
        if path.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
            parent = self.parent()
            if parent and hasattr(parent, "load_from_path"):
                parent.load_from_path(path)
