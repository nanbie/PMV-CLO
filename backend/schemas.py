from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SensorDataBase(BaseModel):
    temperature: float
    humidity: float
    air_velocity: float
    mean_radiant_temperature: Optional[float] = None

class SensorDataCreate(SensorDataBase):
    pass

class SensorData(SensorDataBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

class PMVRequest(BaseModel):
    # 如果用户想基于特定传感器数据计算，可以传 sensor_id，或者直接传环境参数
    # 这里设计为：前端获取了传感器数据，然后结合 CLO 策略发回给后端计算
    # 或者：前端只传 CLO 策略，后端取最新传感器数据计算。后者更符合“后端读取数据库”的描述。
    
    clo_strategy: str  # "fixed_summer", "fixed_winter", "dynamic_temp", "manual"
    manual_clo: Optional[float] = 0.5
    metabolic_rate: float = 1.0  # met
    
class PMVResponse(BaseModel):
    pmv: float
    ppd: float
    clo: float
    ta: float
    rh: float
    vel: float


class PMVManualRequest(BaseModel):
    ta: float
    rh: float
    vel: float
    tr: float
    clo: float
    met: float = 1.0
