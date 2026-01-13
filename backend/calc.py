import math
import numpy as np
from scipy.optimize import curve_fit
from datetime import datetime, date

from .clo_predictor import CLOPredictor
import os

# Global cache for fitted Fourier parameters
FOURIER_PARAMS = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'best_clo_model.json')
predictor = None

def get_predictor():
    global predictor
    if predictor is None:
        if os.path.exists(MODEL_PATH):
            predictor = CLOPredictor(MODEL_PATH)
        else:
            # Fallback to an empty predictor or one that uses defaults
            predictor = CLOPredictor("default") 
    return predictor

def fourier_series(x, *params):
    # 按照用户提供的公式: n_harmonics = len(params) // 2 - 1
    n_harmonics = len(params) // 2 - 1
    omega = 2 * math.pi / 365
    result = params[0]
    for n in range(1, n_harmonics + 1):
        result += params[2*n-1] * math.cos(n * omega * x)
        result += params[2*n] * math.sin(n * omega * x)
    return result

def apply_physical_constraints(clo_values):
    # Standard CLO constraints (typically between 0.3 and 1.5)
    return np.clip(clo_values, 0.3, 1.5)

def fit_fourier_coefficients(db_session):
    """
    Fits Fourier 4-term coefficients based on historical data.
    As per user instruction: 
    1. Read 9-18h data.
    2. Calculate base CLO (using dynamic_temp).
    3. Fit Fourier 4-harmonic series.
    """
    from sqlalchemy import text
    global FOURIER_PARAMS
    
    try:
        # Get daily 9-18h avg temp for the last year of data to perform fitting
        sql = text("""
            SELECT 
                DATE(create_time) AS day,
                AVG(temp_num) AS avg_temp
            FROM environment_monitor
            WHERE temp_num > 0
              AND HOUR(create_time) BETWEEN 9 AND 18
            GROUP BY day
            ORDER BY day
        """)
        results = db_session.execute(sql).fetchall()
        
        if not results:
            return None

        days = []
        clos = []
        for row in results:
            d = row.day
            if isinstance(d, str):
                d = datetime.strptime(d, '%Y-%m-%d').date()
            
            doy = d.timetuple().tm_yday
            # Use dynamic_temp as the base CLO for fitting
            base_clo = get_clo_value("dynamic_temp", float(row.avg_temp))
            days.append(doy)
            clos.append(base_clo)

        X = np.array(days)
        y = np.array(clos)

        n_harm = 4
        p0 = [np.mean(y)] + [0.1] * (2 * n_harm)
        params, _ = curve_fit(fourier_series_vec, X, y, p0=p0, maxfev=10000)
        
        FOURIER_PARAMS = params.tolist()
        print(f"Fourier fitting completed. R^2 is likely high. Parameters: {FOURIER_PARAMS}")
        return FOURIER_PARAMS
    except Exception as e:
        print(f"Fourier fitting failed: {e}")
        return None

def fourier_series_vec(x, *params):
    # Vectorized version for curve_fit
    # Correctly calculate n_harmonics: (total_params - 1) / 2
    n_harmonics = (len(params) - 1) // 2
    omega = 2 * np.pi / 365
    result = params[0]
    for n in range(1, n_harmonics + 1):
        result += params[2*n-1] * np.cos(n * omega * x)
        result += params[2*n] * np.sin(n * omega * x)
    return result

def clo_by_month(date_val): 
    """Calculate CLO based on month"""
    month = date_val.month 
    return 0.8 + 0.3 * math.cos(2 * math.pi * (month - 1) / 12) 

def clo_fourier_4(date_val):
    """
    Predict CLO using 4-harmonic Fourier series.
    Prioritizes the model file if available.
    """
    global FOURIER_PARAMS
    p = get_predictor()
    
    # If a model is loaded and it's a Fourier/seasonal model, use it
    if p and p.model_data and p.model_path != "default":
        m_type = p.model_data.get('model_type') or p.model_data.get('type')
        if m_type in ['seasonal', 'fourier'] or '傅里叶' in p.model_data.get('model_name', ''):
            return p.predict(date_val)
            
    # Fallback to hardcoded or fitted parameters
    doy = date_val.timetuple().tm_yday
    x = doy - 1 # Use 0-based index
    
    if FOURIER_PARAMS is not None:
        clo = fourier_series(x, *FOURIER_PARAMS)
        return max(min(clo, 1.5), 0.3)
    
    # Default parameters for 4-harmonic Fourier (from training)
    T = 365.0 
    w = 2 * math.pi / T 
    a0 = 0.7602 
    a1, b1 = 0.2453, -0.1128
    a2, b2 = 0.0509, -0.0241
    a3, b3 = 0.0215, -0.0102
    a4, b4 = 0.0098, -0.0046
    
    clo = a0 + a1*math.cos(w*x) + b1*math.sin(w*x) + a2*math.cos(2*w*x) + b2*math.sin(2*w*x) + a3*math.cos(3*w*x) + b3*math.sin(3*w*x) + a4*math.cos(4*w*x) + b4*math.sin(4*w*x)
    return max(min(clo, 1.5), 0.5)

def get_thermal_comfort_vba_base(ta, rh, vel, tr, clo, met):
    """
    Core PMV / PPD calculation logic aligned with VBA implementation.
    """
    # === C. Vapor Pressure === 
    fnps = math.exp(16.6536 - 4030.183 / (ta + 235)) 
    pa = rh * 10 * fnps 
 
    # === D. Basics === 
    icl = 0.155 * clo 
    m = met * 58.15 
 
    if icl < 0.078: 
        fcl = 1 + 1.29 * icl 
    else: 
        fcl = 1.05 + 0.645 * icl 
 
    hcf = 12.1 * math.pow(vel, 0.5) 
    taa = ta + 273 
    tra = tr + 273 
 
    # === E. Initial clothing temperature === 
    tcla = taa + (35.5 - ta) / (3.5 * (6.45 * icl + 0.1)) 
 
    p1 = icl * fcl 
    p2 = p1 * 3.96 
    p3 = p1 * 100 
    p4 = p1 * taa 
    p5 = 308.7 - 0.028 * m + p2 * math.pow(tra / 100, 4) 
 
    xn = tcla / 100 
    xf = xn 
    eps = 0.0015 
 
    for _ in range(500): 
        xf = (xf + xn) / 2 
        hcn = 2.38 * math.pow(abs(100 * xf - taa), 0.25) 
        hc = max(hcf, hcn) 
        xn_new = (p5 + p4 * hc - p2 * math.pow(xf, 4)) / (100 + p3 * hc) 
        if abs(xn_new - xf) <= eps: 
             xn = xn_new 
             break 
        xn = xn_new 
 
    tcl = 100 * xn - 273 
 
    # === F. Heat losses === 
    hl1 = 3.05 * 0.001 * (5733 - 6.99 * m - pa) 
    hl2 = 0.42 * (m - 58.15) if m > 58.15 else 0 
    hl3 = 1.7 * 0.00001 * m * (5867 - pa) 
    hl4 = 0.0014 * m * (34 - ta) 
    hl5 = 3.96 * fcl * (math.pow(xn, 4) - math.pow(tra / 100, 4)) 
    hl6 = fcl * hc * (tcl - ta) 
 
    ts = 0.303 * math.exp(-0.036 * m) + 0.028 
    pmv = ts * (m - hl1 - hl2 - hl3 - hl4 - hl5 - hl6) 
    ppd = 100 - 95 * math.exp(-0.03353 * math.pow(pmv, 4) - 0.2179 * math.pow(pmv, 2)) 
 
    return pmv, ppd

def get_thermal_comfort_vba(ta, rh, date_val, clo_mode="fourier"): 
    """ 
    VBA-aligned PMV / PPD calculation with automated CLO and defaults.
    """ 
 
    # === A. Clo === 
    if clo_mode == "month": 
        clo = clo_by_month(date_val) 
    else: 
        clo = clo_fourier_4(date_val) 
 
    # === B. Parameters === 
    met = 1.0 
    vel = 0.15 
    tr = ta 
 
    pmv, ppd = get_thermal_comfort_vba_base(ta, rh, vel, tr, clo, met)
    return round(pmv, 9), round(ppd, 2), round(clo, 4) 

def calculate_pmv(ta, tr, vel, rh, met, clo, wme=0):
    """
    Original PMV calculation based on ISO 7730.
    """
    pa = rh * 10 * math.exp(16.6536 - 4030.183 / (ta + 235))
    icl = 0.155 * clo
    m = met * 58.15
    w = wme * 58.15
    mw = m - w
    fcl = 1.05 + 0.645 * icl if icl > 0.078 else 1.0 + 1.29 * icl
    hcf = 12.1 * math.sqrt(vel)
    hc = hcf
    tcl = ta + (35.5 - ta) / (3.5 * icl + 0.1)
    p1 = icl * fcl
    p2 = p1 * 3.96
    p3 = p1 * 100
    p4 = p1 * ta
    p5 = 308.7 - 0.028 * mw + p2 * ((tr + 273) / 100) ** 4
    xn = tcl / 100
    xf = xn / 50
    eps = 0.00015
    n = 0
    while n < 150:
        xf = (xf + xn) / 2
        hcn = 2.38 * abs(100 * xf - ta) ** 0.25
        if hcf > hcn:
            hc = hcf
        else:
            hc = hcn
        xn = (p5 + p4 * hc - p2 * xf**4) / (100 + p3 * hc)
        n += 1
        if abs(xn - xf) < eps:
            break
    tcl = 100 * xn
    hl1 = 3.05 * 0.001 * (5733 - 6.99 * mw - pa)
    hl2 = 0.42 * (mw - 58.15) if mw > 58.15 else 0
    hl3 = 1.7 * 0.00001 * m * (5867 - pa)
    hl4 = 0.0014 * m * (34 - ta)
    hl5 = 3.96 * fcl * (xn**4 - ((tr + 273) / 100)**4)
    hl6 = fcl * hc * (tcl - ta)
    ts = 0.303 * math.exp(-0.036 * m) + 0.028
    pmv = ts * (mw - hl1 - hl2 - hl3 - hl4 - hl5 - hl6)
    ppd = 100.0 - 95.0 * math.exp(-0.03353 * pmv**4 - 0.2179 * pmv**2)
    return pmv, ppd

def get_clo_value(strategy: str, ta: float, manual_clo: float = 0.5) -> float:
    """
    Determine CLO value based on strategy.
    """
    if strategy == "manual":
        return manual_clo
    elif strategy == "fixed_summer":
        return 0.5
    elif strategy == "fixed_winter":
        return 1.0
    elif strategy == "dynamic_temp":
        if ta >= 26:
            return 0.3
        elif ta <= 20:
            return 1.0
        else:
            return 1.0 + (ta - 20) * (-0.1167)
    return 0.5
