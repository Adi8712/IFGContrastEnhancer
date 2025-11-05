import cv2
import numpy as np

def entropy(gray):
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    p = hist / hist.sum()
    p = p[p > 0]
    return -np.sum(p * np.log2(p))

def contrast(gray):
    arr = gray.astype(np.float32)
    return np.sqrt(np.mean((arr - arr.mean())**2))
 
def cii(og_gray, enc_gray):
    return contrast(enc_gray) / (contrast(og_gray) + 1e-9)