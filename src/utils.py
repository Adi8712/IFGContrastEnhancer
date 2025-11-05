import numpy as np

def normalise(x):
    x = x.astype(np.float32)
    return(x - x.min()) / (x.max() - x.min() + 1e-9)