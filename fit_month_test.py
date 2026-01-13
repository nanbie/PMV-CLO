
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
import math

def clo_by_month(doy):
    # Rough month estimation from doy
    month = (doy - 1) // 30 + 1
    if month > 12: month = 12
    return 0.8 + 0.3 * math.cos(2 * math.pi * (month - 1) / 12)

def fourier_series(x, *params):
    n_harmonics = len(params) // 2 - 1
    omega = 2 * np.pi / 365
    result = params[0]
    for n in range(1, n_harmonics + 1):
        result += params[2*n-1] * np.cos(n * omega * x)
        result += params[2*n] * np.sin(n * omega * x)
    return result

X = np.arange(1, 366)
y = np.array([clo_by_month(d) for d in X])

n_harm = 4
p0 = [y.mean()] + [0.1] * (2 * n_harm)
params, _ = curve_fit(fourier_series, X, y, p0=p0, maxfev=10000)

val_01_01 = fourier_series(1, *params)
print(f"Fit on month strategy - doy=1 value: {val_01_01}")
print(f"Params: {params.tolist()}")
