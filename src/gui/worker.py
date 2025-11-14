"""Background worker thread for processing images"""

from typing import Tuple, Any
from PySide6.QtCore import QThread, Signal
import numpy as np

from src.enhancements import clahe_apply, ifg_enhance


class Worker(QThread):
    """Worker that runs enhancement algorithms off the GUI thread

    Emits:
        done(clahe_img: np.ndarray, ifg_img: np.ndarray, k: float)
    """
    done = Signal(object, object, float)

    def __init__(self, img: np.ndarray, clip: float = 2.0):
        super().__init__()
        self._img = img.copy() if img is not None else None
        self._clip = float(clip)

    def run(self) -> None:
        if self._img is None:
            return
        clahe_img = clahe_apply(self._img, clip=self._clip)
        ifg_img, k = ifg_enhance(self._img, clip=self._clip)
        self.done.emit(clahe_img, ifg_img, k)
