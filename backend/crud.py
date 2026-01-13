from sqlalchemy.orm import Session
from . import models, schemas

def get_latest_sensor_data(db: Session):
    return db.query(models.SensorData).order_by(models.SensorData.timestamp.desc()).first()

def create_sensor_data(db: Session, sensor_data: schemas.SensorDataCreate):
    # If mean_radiant_temperature is not provided, assume it equals temperature
    tr = sensor_data.mean_radiant_temperature
    if tr is None:
        tr = sensor_data.temperature
        
    db_item = models.SensorData(
        temperature=sensor_data.temperature,
        humidity=sensor_data.humidity,
        air_velocity=sensor_data.air_velocity,
        mean_radiant_temperature=tr
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item
