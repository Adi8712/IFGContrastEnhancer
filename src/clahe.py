import cv2
 
def apply(img, clip=2.0, grid=(8,8)):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h,s,v = cv2.split(hsv)
    clahe = cv2.createCLAHE(clip, grid)
    v2 = clahe.apply(v)
    hsv2 = cv2.merge([h,s,v2])
    return cv2.cvtColor(hsv2, cv2.COLOR_HSV2BGR)