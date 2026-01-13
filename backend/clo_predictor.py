import json
import math
import numpy as np
import os
from datetime import datetime

class CLOPredictor:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model_data = None
        self.load_model()

    def load_model(self):
        # Try to find the model file in several locations
        search_paths = [
            self.model_path,
            os.path.join('models', self.model_path),
            os.path.join('backend', 'models', self.model_path),
            os.path.join(os.path.dirname(__file__), 'models', self.model_path)
        ]
        
        for path in search_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        self.model_data = json.load(f)
                    self.model_path = path
                    print(f"Successfully loaded model from {path}")
                    return
                except Exception as e:
                    print(f"Error reading model from {path}: {e}")

        # Fallback to default coefficients if file not found
        print(f"Model file not found in search paths. Using defaults.")
        self.model_data = {
                "name": "Fourier 4-Harmonic Default",
                "type": "fourier",
                "harmonics": 4,
                "params": [
                    0.7602,  # a0
                    0.2453, -0.1128,  # a1, b1
                    0.0509, -0.0241,  # a2, b2
                    0.0215, -0.0102,  # a3, b3
                    0.0098, -0.0046   # a4, b4
                ]
            }

    def info(self):
        print("--- CLO Predictor Info ---")
        print(f"Model Path: {self.model_path}")
        if self.model_data:
            print(f"Model Name: {self.model_data.get('model_name', 'N/A')}")
            print(f"Model Type: {self.model_data.get('model_type', 'Unknown')}")
            print(f"R2 Score: {self.model_data.get('r2_score', 'N/A')}")
        print("--------------------------")

    def fourier_series(self, x, params):
        # 按照用户提供的公式: n_harmonics = len(params) // 2 - 1
        # 对于 9 个参数，这会计算到 3 次谐波 (忽略最后两个 0.1)
        n_harmonics = len(params) // 2 - 1
        omega = 2 * math.pi / 365
        result = params[0]
        for n in range(1, n_harmonics + 1):
            result += params[2*n-1] * math.cos(n * omega * x)
            result += params[2*n] * math.sin(n * omega * x)
        return result

    def predict(self, date_str):
        """预测指定日期的 CLO 值"""
        if isinstance(date_str, str):
            try:
                dt = datetime.strptime(date_str, '%Y-%m-%d')
            except ValueError:
                dt = datetime.strptime(date_str, '%Y/%m/%d')
        else:
            dt = date_str
            
        # 使用 0-based day of year (x = doy - 1)
        doy = dt.timetuple().tm_yday
        x = doy - 1
        
        if self.model_data:
            params = self.model_data.get('model_params') or self.model_data.get('params')
            m_type = self.model_data.get('model_type') or self.model_data.get('type')
            
            # 检查是否是傅里叶/季节性模型
            if params and (m_type == 'seasonal' or m_type == 'fourier' or '傅里叶' in self.model_data.get('model_name', '')):
                clo = self.fourier_series(x, params)
                # 物理约束：CLO 通常在 0.3 到 1.5 之间
                return max(min(clo, 1.5), 0.3)
        
        # 兜底方案
        return 0.5
