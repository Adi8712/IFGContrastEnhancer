import cv2, glob, random
from .metrics import entropy, cii
from .clahe import apply
from .ifg import enhance

def run(): 
    img_path = random.choice(glob.glob("data/*"))
    print("Using:", img_path)
    img = cv2.imread(img_path)
    
    og_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    img_clahe = apply(img)
    img_ifg, k = enhance(img)
    
    enc_gray = cv2.cvtColor(img_clahe, cv2.COLOR_BGR2GRAY)
    gray_ifg = cv2.cvtColor(img_ifg, cv2.COLOR_BGR2GRAY)
    
    print("\nChosen k:", k)
    print("Entropy\nOriginal:", entropy(og_gray), "CLAHE:", entropy(enc_gray), "IFG:", entropy(gray_ifg))
    print("CII\nCLAHE:", cii(og_gray, enc_gray),"IFG:", cii(og_gray, gray_ifg))
    
    cv2.imshow("Original", img)
    cv2.imshow("CLAHE Baseline", img_clahe)
    cv2.imshow("IFG + CLAHE (Paper Method)", img_ifg)
    cv2.waitKey(0)