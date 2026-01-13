from sqlalchemy import Column, Integer, Float, DateTime, String, cast
from sqlalchemy.sql import func
from .database import Base

class EnvironmentMonitor(Base):
    __tablename__ = "environment_monitor"

    # 虽然原表可能没有自增主键，但在 SQLAlchemy 中必须定义一个主键
    # 如果没有物理主键，可以将 create_time 和 dev_id 视为复合主键
    create_time = Column(DateTime, primary_key=True)
    dev_id = Column(String(255), primary_key=True)
    
    temp_num = Column(String(255)) # 原始表是 varchar
    rh_num = Column(String(255))   # 原始表是 varchar
    tvoc_num = Column(String(255))
    pm_num = Column(String(255))
    co2_num = Column(String(255))
    product_key = Column(String(255))
    project_id = Column(String(64))
    space_id = Column(Integer)

    @property
    def temperature(self):
        try:
            return float(self.temp_num) if self.temp_num else None
        except ValueError:
            return None

    @property
    def humidity(self):
        try:
            return float(self.rh_num) if self.rh_num else None
        except ValueError:
            return None
