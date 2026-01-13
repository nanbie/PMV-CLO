import sys
import os

# Add the parent directory to sys.path to allow importing from backend module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import SessionLocal
from sqlalchemy import text
import pandas as pd

def check_data():
    db = SessionLocal()
    try:
        print("Connecting to database...")
        # 1. Check if table exists and show columns
        try:
            result = db.execute(text("DESCRIBE environment_monitor"))
            print("\nTable 'environment_monitor' structure:")
            for row in result:
                print(row)
        except Exception as e:
            print(f"\nError checking table structure: {e}")

        # 2. Check sample data
        print("\nChecking sample data (first 5 rows):")
        try:
            result = db.execute(text("SELECT * FROM environment_monitor LIMIT 5"))
            rows = result.fetchall()
            if not rows:
                print("Table is empty!")
            else:
                for row in rows:
                    print(row)
        except Exception as e:
            print(f"Error fetching sample data: {e}")

        # 3. Run the specific aggregation query
        print("\nRunning aggregation query...")
        sql_query = text("""
            SELECT 
                 t.report_date, 
                 t.report_hour, 
                 AVG(t.hour_temp) AS final_temp_avg, 
                 AVG(t.hour_tvoc) AS final_tvoc_avg, 
                 AVG(t.hour_pm)   AS final_pm_avg, 
                 AVG(t.hour_co2)  AS final_co2_avg, 
                 AVG(t.hour_rh)   AS final_rh_avg, 
                 COUNT(t.dev_id)  AS device_count 
             FROM ( 
                 SELECT 
                     DATE(create_time) AS report_date, 
                     HOUR(create_time) AS report_hour, 
                     dev_id, 
                     AVG(temp_num) AS hour_temp, 
                     AVG(tvoc_num) AS hour_tvoc, 
                     AVG(pm_num)   AS hour_pm, 
                     AVG(co2_num)  AS hour_co2, 
                     AVG(rh_num)   AS hour_rh 
                 FROM environment_monitor 
                 WHERE dev_id IN ( 
                     'SJ-A0-C01-14F-00-HL-CGQ-0005', 'SJ-A0-C01-14F-00-HL-CGQ-0006', 
                     'SJ-A0-C01-14F-00-HL-CGQ-0008', 'SJ-A0-C01-14F-00-HL-CGQ-0007', 
                     'SJ-A0-C01-14F-00-HL-CGQ-0009', 'SJ-A0-C01-14F-00-HL-CGQ-0004', 
                     'SJ-A0-C01-14F-00-HL-CGQ-0003', 'SJ-A0-C01-14F-00-HL-CGQ-0002', 
                     'SJ-A0-C01-14F-00-HL-CGQ-0001', 'SJ-A0-C01-14F-00-HL-CGQ-0010' 
                 ) 
                   AND create_time >= '2024-12-01' 
                   AND create_time < '2025-12-01' 
                   AND HOUR(create_time) BETWEEN 9 AND 18 
                   AND temp_num > 0 
                   AND rh_num > 0 
                   AND co2_num > 0 
                 GROUP BY DATE(create_time), HOUR(create_time), dev_id 
             ) AS t 
             GROUP BY t.report_date, t.report_hour 
             ORDER BY t.report_date ASC, t.report_hour ASC;
        """)
        
        result = db.execute(sql_query)
        rows = result.fetchall()
        print(f"\nAggregation Query Result Count: {len(rows)}")
        if rows:
            print("First 5 aggregated rows:")
            for row in rows[:5]:
                print(row)
                
    except Exception as e:
        print(f"\nCritical Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_data()
