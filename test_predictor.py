import sys
import os
from datetime import datetime

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from clo_predictor import CLOPredictor

def example_custom_dates(): 
    """自定义日期预测示例""" 
    print("\n" + "="*70) 
    print("示例6: 自定义日期预测".center(70)) 
    print("="*70) 
    
    # 直接使用文件名，CLOPredictor 内部会处理路径搜索
    predictor = CLOPredictor('best_clo_model.json') 
    
    # 特殊日期预测 
    special_dates = { 
        '2025-01-01': '元旦', 
        '2025-02-10': '春节', 
        '2025-05-01': '劳动节', 
        '2025-06-01': '儿童节', 
        '2025-10-01': '国庆节', 
        '2025-12-25': '圣诞节' 
    } 
    
    print("\n【节假日CLO预测】") 
    for date, holiday in special_dates.items(): 
        clo = predictor.predict(date) 
        print(f"  {date} ({holiday}): CLO = {clo:.4f}") 

if __name__ == "__main__":
    example_custom_dates()
