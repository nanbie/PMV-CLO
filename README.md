# PMV-CLO 环境监测与热舒适度分析系统

本项目是一个集成了环境数据监测、PMV（热感觉指标）计算及可视化分析的全栈系统。支持按楼层、分区过滤数据，并提供每日趋势、每时刻热力分布及 CSV 数据导出功能。

## 项目结构

- `backend/`: 基于 FastAPI 的后端 API，负责数据处理、PMV 计算（傅里叶拟合服装热阻算法）及数据库交互。
- `frontend/`: 基于 Vue 3 + Vite + ECharts 的前端展示界面，提供响应式数据可视化。

## 环境要求

- **后端**: Python 3.10+
- **前端**: Node.js 18+ (推荐 20+)
- **数据库**: MySQL 5.7+ 或 8.0+

## 快速开始

### 1. 后端配置与运行

1. 进入后端目录：
   ```bash
   cd backend
   ```
2. 创建并激活虚拟环境（推荐）：
   ```bash
   python -m venv venv
   # Windows
   .\venv\Scripts\activate
   # Linux/macOS
   source venv/bin/activate
   ```
3. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
4. 环境变量配置：
   在项目根目录（或 `backend/` 目录下）创建 `.env` 文件，配置数据库连接信息：
   ```env
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_HOST=
   DB_PORT=
   DB_NAME=
   ```
5. 启动后端服务：
   ```bash
   uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

### 2. 前端配置与运行

1. 进入前端目录：
   ```bash
   cd frontend
   ```
2. 安装依赖：
   ```bash
   npm install
   ```
3. 启动开发服务器：
   ```bash
   npm run dev
   ```
4. 访问页面：
   打开浏览器访问 `http://localhost:5173` (具体端口见终端输出)。

## 主要功能

- **PMV 计算器**: 输入六个环境参数（温度、湿度、风速、辐射温度、服装热阻、代谢率）实时计算 PMV/PPD。
- **全局策略切换**: 支持傅里叶拟合、按月固定、手动输入等多种服装热阻计算策略。
- **楼层分区过滤**: 支持 6层、7层、8层、9层、12层及 14层传感器设备的定向数据分析。
- **精细化图表**:
  - **每时刻 PMV 分布**: 9:00 - 18:00 的小时级热力分布，附带舒适度分级统计结果。
  - **每日趋势图**: 环境指标（温度、湿度）的历史变化曲线。
  - **日历热力图**: 以日历形式展示全年的舒适度概况。
- **数据导出**: 支持将 9:00 - 18:00 的小时级环境与舒适度原始数据导出为 CSV 文件。

## 数据库说明

系统依赖 `environment_monitor` 表，包含以下核心字段：
- `dev_id`: 设备唯一标识
- `create_time`: 记录时间
- `temp_num`: 温度值
- `rh_num`: 相对湿度值

## 辅助工具脚本

根目录下包含一些用于算法验证和测试的脚本：
- `test_predictor.py`: 测试 PMV 预测器和模型加载是否正常。
- `fit_clo_diagnostic.py`: 傅里叶拟合算法的诊断与可视化脚本。
- `fit_month_test.py`: 按月固定策略的测试脚本。

## 部署建议

- **生产环境**: 建议使用 Nginx 反向代理前端静态文件，并使用 Gunicorn + Uvicorn 部署后端。
- **跨域配置**: 后端已开启全域名 CORS，如需限制请修改 `backend/main.py` 中的 `allow_origins`。

## 技术栈

- **Backend**: FastAPI, SQLAlchemy, PyMySQL, Uvicorn
- **Frontend**: Vue 3 (Composition API), Vite, ECharts, Axios, Vue-ECharts
- **Algorithms**: 基于傅里叶级数的服装热阻预测算法，ISO 7730 标准 PMV 计算逻辑
