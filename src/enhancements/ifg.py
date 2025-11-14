"""IFG-based enhancement algorithm (implementation adapted from the paper)

Provides `enhance(img, clip=2.0)` which returns (enhanced_bgr, k_used)
"""

from typing import Tuple
import numpy as np
import cv2


def _entropy(gray: np.ndarray) -> float:
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    p = hist / (hist.sum() + 1e-12)
    p = p[p > 0]
    return float(-np.sum(p * np.log2(p)))


def _normalise(x: np.ndarray) -> np.ndarray:
    a = x.astype(np.float32)
    mn = a.min()
    mx = a.max()
    denom = (mx - mn) if (mx - mn) != 0 else 1.0
    return (a - mn) / denom


def _compute(norm: np.ndarray, k: float) -> np.ndarray:
    mu = np.power(norm, k)
    nu = np.power(1.0 - norm, k)
    pi = 1.0 - mu - nu
    return mu + pi


def _choose_k(norm: np.ndarray) -> float:
    # Search grid as described in the paper: 0.1 .. 0.95 step 0.05
    best_k = 0.1
    best_entropy = -1.0
    for k in np.arange(0.1, 1.0, 0.05):
        ifi = _compute(norm, float(k))
        gray = (np.clip(ifi * 255.0, 0, 255)).astype(np.uint8)
        e = _entropy(gray)
        if e > best_entropy:
            best_entropy = e
            best_k = float(k)
    return best_k


def enhance(img: np.ndarray, clip: float = 2.0) -> Tuple[np.ndarray, float]:
    """
    Enhance a BGR image using the IFG -> CLAHE pipeline.

    Returns:
        (enhanced_bgr, k_used)
    """
    if img is None:
        raise ValueError("img must be a valid image array")

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    norm = _normalise(v)
    k = _choose_k(norm)
    ifi = _compute(norm, k)
    ifi_img = (np.clip(ifi * 255.0, 0, 255)).astype(np.uint8)

    clahe = cv2.createCLAHE(clipLimit=float(clip), tileGridSize=(8, 8))
    enhanced = clahe.apply(ifi_img)

    enhanced_norm = (_normalise(enhanced) * 255.0).astype(np.uint8)

    hsv2 = cv2.merge([h, s, enhanced_norm])
    return cv2.cvtColor(hsv2, cv2.COLOR_HSV2BGR), float(k)
