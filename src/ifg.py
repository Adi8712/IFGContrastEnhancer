import cv2
import numpy as np

def entropy(gray):
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).ravel()
    p = hist / hist.sum()
    p = p[p > 0]
    return -np.sum(p * np.log2(p))
 
def normalise(x):
    x = x.astype(np.float32)
    return(x - x.min()) / (x.max() - x.min() + 1e-9)

def compute(norm, k):
    mu = norm ** k
    nu = (1 - norm) ** k
    pi = 1 - mu - nu
    return mu + pi
 
def chooseK(norm):
    i, j = 0, -1
    for k in np.arange(0.1, 1.0, 0.05):    # paper uses search-based optimization
        ifi = compute(norm, k)
        e = entropy((ifi * 255).astype(np.uint8))
        if e > j:
            j = e
            i = k
    return i
 
def enhance(img, clip=2.0):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h,s,v = cv2.split(hsv)
    norm = normalise(v)
 
    k = chooseK(norm)
    ifi = compute(norm, k)
    ifi = (ifi * 255).astype(np.uint8)
 
    clahe = cv2.createCLAHE(clip, (8,8))
    enhanced = clahe.apply(ifi)
 
    enhanced = (normalise(enhanced) * 255).astype(np.uint8)
 
    hsv2 = cv2.merge([h,s,enhanced])
    return cv2.cvtColor(hsv2, cv2.COLOR_HSV2BGR), k