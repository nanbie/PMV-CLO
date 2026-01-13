from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# 加载 .env 文件
# 尝试显式指定路径，确保加载正确
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"Loaded .env from {dotenv_path}")
else:
    load_dotenv() # Fallback to default
    print("Loaded .env from default location (or failed if not found)")

# 默认使用 MySQL 配置
# 格式: mysql+pymysql://user:password@host:port/dbname
# 请根据实际情况修改下面的配置，或者设置环境变量
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "pmv_db")

print(f"Connecting to Database: {DB_HOST}:{DB_PORT} as {DB_USER}")

# 对密码进行 URL 编码，防止特殊字符导致连接失败
import urllib.parse
encoded_password = urllib.parse.quote_plus(DB_PASSWORD)

SQLALCHEMY_DATABASE_URL = f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    # Test connection immediately
    with engine.connect() as connection:
        print("Database connection successful!")
except Exception as e:
    print(f"Database connection failed during setup: {e}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
