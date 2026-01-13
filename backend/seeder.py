import random
import datetime
import math
from sqlalchemy.orm import Session
from . import models, schemas, crud, database

def seed_yearly_data(db: Session):
    """
    Generates mock sensor data for a full year (2025).
    Focuses on 9:00 - 18:00 daily.
    Simulates seasonal temperature variations.
    """
    # Check if data already exists to avoid duplication
    if db.query(models.SensorData).count() > 1000:
        print("Data likely already seeded. Skipping.")
        return

    print("Seeding yearly data... this may take a moment.")
    
    start_date = datetime.date(2025, 1, 1)
    end_date = datetime.date(2025, 12, 31)
    delta = datetime.timedelta(days=1)
    
    current_date = start_date
    batch = []
    
    while current_date <= end_date:
        # Seasonality: 
        # Jan (0) -> Coldest
        # July (6) -> Hottest
        # Cosine wave: -cos(x) peaks at pi (halfway)
        
        day_of_year = current_date.timetuple().tm_yday
        # Normalized 0 to 2pi
        season_factor = (day_of_year / 365.0) * 2 * math.pi
        # Base temp 22, variation +/- 8. Jan/Dec cold, July hot.
        # -cos(0) = -1 (cold), -cos(pi) = 1 (hot)
        seasonal_temp_base = 22 - 8 * math.cos(season_factor) 
        
        # Working hours 09:00 - 18:00
        for hour in range(9, 19):
            # Daily variation: Cool in morning, Peak at 14:00, Cool in evening
            # 09:00 -> -2, 14:00 -> +3, 18:00 -> +0
            hour_factor = (hour - 9) / 9.0 # 0 to 1
            # Parabola peaking around 0.5
            daily_variation = -2 + 5 * math.sin(hour_factor * math.pi)
            
            # Random noise
            noise = random.uniform(-1.0, 1.0)
            
            final_temp = seasonal_temp_base + daily_variation + noise
            
            # Humidity: Inverse to temp usually
            final_rh = 50 - (daily_variation * 2) + random.uniform(-5, 5)
            final_rh = max(20, min(90, final_rh))
            
            # Velocity: Random
            final_vel = random.uniform(0.05, 0.3)
            
            timestamp = datetime.datetime.combine(current_date, datetime.time(hour, 0))
            
            # Create object (using ORM directly for speed, bypass CRUD overhead if possible, or use bulk)
            data = models.SensorData(
                timestamp=timestamp,
                temperature=final_temp,
                humidity=final_rh,
                air_velocity=final_vel,
                mean_radiant_temperature=final_temp # Assume Tr = Ta
            )
            batch.append(data)
            
        current_date += delta
        
        # Batch insert every month or so to manage memory
        if len(batch) > 500:
            db.add_all(batch)
            db.commit()
            batch = []
            
    if batch:
        db.add_all(batch)
        db.commit()
        
    print("Seeding complete.")
