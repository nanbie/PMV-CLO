
import sys
import os
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from datetime import datetime, date
from sqlalchemy import text

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), 'backend'))
from backend import database, calc

def fourier_series(x, *params):
    n_harmonics = len(params) // 2 - 1
    omega = 2 * np.pi / 365
    result = params[0]
    for n in range(1, n_harmonics + 1):
        result += params[2*n-1] * np.cos(n * omega * x)
        result += params[2*n] * np.sin(n * omega * x)
    return result

def fit_clo_data():
    db = database.SessionLocal()
    try:
        # 1. Get daily 9-18h average temperature for 2025
        sql = text("""
            SELECT 
                DATE(create_time) AS day,
                AVG(temp_num) AS avg_temp
            FROM environment_monitor
            WHERE create_time >= '2025-01-01' AND create_time <= '2025-12-31'
              AND HOUR(create_time) BETWEEN 9 AND 18
              AND temp_num > 0
            GROUP BY day
            ORDER BY day
        """)
        results = db.execute(sql).fetchall()
        
        if not results:
            print("No data found for 2025 fitting.")
            return

        data = []
        for row in results:
            d = row.day
            if isinstance(d, str):
                d = datetime.strptime(d, '%Y-%m-%d').date()
            
            doy = d.timetuple().tm_yday
            # Calculate base CLO using dynamic_temp strategy
            clo_base = calc.get_clo_value("dynamic_temp", float(row.avg_temp))
            data.append({'doy': doy, 'clo': clo_base})

        df = pd.DataFrame(data)
        X = df['doy'].values
        y = df['clo'].values

        # 2. Fit 4-term Fourier series
        n_harm = 4
        p0 = [y.mean()] + [0.1] * (2 * n_harm)
        params, _ = curve_fit(fourier_series, X, y, p0=p0, maxfev=10000)

        print("--- Fitting Results ---")
        print(f"Params: {params.tolist()}")
        
        # 3. Verify 2025-01-01 (doy=1)
        val_01_01 = fourier_series(1, *params)
        print(f"Value for 2025-01-01 (doy=1): {val_01_01}")
        print(f"Target Value: 1.05608654438627")

    finally:
        db.close()

if __name__ == "__main__":
    fit_clo_data()
