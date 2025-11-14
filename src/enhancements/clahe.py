"""Simple CLAHE-based enhancement helper

This module provides a single function `apply` that applies CLAHE to the V
(channel) of an image in BGR (OpenCV) space and returns a BGR image
"""

from typing import Tuple
import numpy as np
import cv2


def apply(img: np.ndarray, clip: float = 2.0, grid: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Apply CLAHE to the V channel of a BGR image.

    Parameters
    ----------
    img : np.ndarray
        Input image in BGR color order (as used by OpenCV).
    clip : float
        CLAHE clip limit.
    grid : tuple[int, int]
        CLAHE tile grid size.

    Returns
    -------
    np.ndarray
        Enhanced image in BGR color order.
    """
    if img is None:
        raise ValueError("img must be a valid image array")

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    clahe = cv2.createCLAHE(clipLimit=float(clip), tileGridSize=grid)
    v2 = clahe.apply(v)

    hsv2 = cv2.merge([h, s, v2])
    return cv2.cvtColor(hsv2, cv2.COLOR_HSV2BGR)
