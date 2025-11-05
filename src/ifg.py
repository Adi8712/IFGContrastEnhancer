import cv2
import numpy as np
from .utils import normalize
from .metrics import entropy
 
def compute(norm, k):
    mu = norm ** k
    nu = (1 - norm) ** k
    pi = 1 - mu - nu
    return mu + pi
 
def k(norm):
    best_k, best_e = 0, -1
    for k in np.arange(0.1, 1.0, 0.05):    # paper uses search-based optimization
        ifi = compute(norm, k)
        e = entropy((ifi * 255).astype(np.uint8))
        if e > best_e:
            best_e = e
            best_k = k
    return best_k
 
def enhance(img, clip=2.0):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h,s,v = cv2.split(hsv)
    norm = normalize(v)
 
    k = k(norm)
    ifi = compute(norm, k)
    ifi = (ifi * 255).astype(np.uint8)
 
    clahe = cv2.createCLAHE(clip, (8,8))
    enhanced = clahe.apply(ifi)
 
    enhanced = (normalize(enhanced) * 255).astype(np.uint8)
 
    hsv2 = cv2.merge([h,s,enhanced])
    return cv2.cvtColor(hsv2, cv2.COLOR_HSV2BGR), k