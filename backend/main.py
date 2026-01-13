from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import date, timedelta, datetime

from . import models, database, schemas, calc

try:
    models.Base.metadata.create_all(bind=database.engine)
except Exception as e:
    print(f"Skipping table creation (likely due to permissions): {e}")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def startup_event():
    db = database.SessionLocal()
    try:
        print("Performing initial Fourier CLO fitting...")
        calc.fit_fourier_coefficients(db)
    finally:
        db.close()

@app.get("/api/export-data")
def export_data(
    start_date: str | None = None,
    end_date: str | None = None,
    city: str | None = "beijing",
    dev_ids: list[str] | None = Query(None),
    db: Session = Depends(get_db),
):
    if start_date and end_date:
        try:
            start_obj = date.fromisoformat(start_date)
            end_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
    else:
        end_obj = date.today()
        start_obj = end_obj - timedelta(days=90)

    start_str = start_obj.isoformat()
    end_str = (end_obj + timedelta(days=1)).isoformat()

    # Base WHERE conditions
    where_conditions = [
        "create_time >= :start_date",
        "create_time < :end_date",
        "HOUR(create_time) BETWEEN 9 AND 18",
        "temp_num > 0",
        "rh_num > 0"
    ]
    query_params = {"start_date": start_str, "end_date": end_str}

    if dev_ids and len(dev_ids) > 0:
        where_conditions.append("dev_id IN :dev_ids")
        query_params["dev_ids"] = tuple(dev_ids)

    where_clause = " AND ".join(where_conditions)

    # Aggregate data to hourly averages (9:00 - 18:00)
    sql_query = text(f"""
        SELECT 
            DATE(create_time) AS day,
            HOUR(create_time) AS hour,
            AVG(temp_num) AS avg_temp,
            AVG(rh_num) AS avg_rh
        FROM environment_monitor
        WHERE {where_clause}
        GROUP BY day, hour
        ORDER BY day, hour
    """)

    try:
        results = db.execute(sql_query, query_params).fetchall()
    except Exception as e:
        print(f"Export query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    export_list = []
    for row in results:
        day_val = row.day
        hour_val = row.hour
        # Ensure day_val is a datetime/date object for calculation
        if isinstance(day_val, str):
            date_obj = datetime.strptime(day_val, "%Y-%m-%d")
        else:
            # If it's a date object, convert to datetime for get_thermal_comfort_vba
            date_obj = datetime.combine(day_val, datetime.min.time())
        
        ta = float(row.avg_temp)
        rh = float(row.avg_rh)
        
        # Calculate PMV/CLO based on the day
        pmv_val, _, clo_val = calc.get_thermal_comfort_vba(
            ta=ta,
            rh=rh,
            date_val=date_obj,
            clo_mode="fourier"
        )
        
        export_list.append({
            "日期": day_val.strftime("%Y-%m-%d") if not isinstance(day_val, str) else day_val,
            "时间": f"{hour_val:02d}:00",
            "温度": round(ta, 2),
            "湿度": round(rh, 1),
            "clo值": round(clo_val, 3),
            "pmv值": round(pmv_val, 3)
        })

    return {"data": export_list}


@app.get("/api/pmv-heatmap")
def get_pmv_heatmap(
    start_date: str | None = None,
    end_date: str | None = None,
    city: str | None = "beijing",
    dev_ids: list[str] | None = Query(None),
    clo_strategy: str = "fourier",
    manual_clo: float = 0.5,
    metabolic_rate: float = 1.0,
    db: Session = Depends(get_db),
):
    if start_date and end_date:
        try:
            start_obj = date.fromisoformat(start_date)
            end_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
    else:
        end_obj = date.today()
        start_obj = end_obj - timedelta(days=90)

    start_str = start_obj.isoformat()
    end_str = (end_obj + timedelta(days=1)).isoformat()

    # Base WHERE conditions
    where_conditions = [
        "create_time >= :start_date",
        "create_time < :end_date",
        "HOUR(create_time) BETWEEN 9 AND 18",
        "temp_num > 0",
        "rh_num > 0"
    ]
    query_params = {"start_date": start_str, "end_date": end_str}

    if dev_ids and len(dev_ids) > 0:
        where_conditions.append("dev_id IN :dev_ids")
        query_params["dev_ids"] = tuple(dev_ids)

    where_clause = " AND ".join(where_conditions)

    sql_query = text(f"""
        SELECT 
            DATE(create_time) AS day,
            AVG(temp_num) AS avg_temp,
            AVG(rh_num) AS avg_rh
        FROM environment_monitor
        WHERE {where_clause}
        GROUP BY day
        ORDER BY day
    """)

    try:
        results = db.execute(sql_query, query_params).fetchall()
    except Exception as e:
        print(f"Calendar query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    heatmap_data = []
    for row in results:
        day_str = str(row.day)
        temp_val = float(row.avg_temp)
        rh_val = float(row.avg_rh)
        
        date_obj = datetime.strptime(day_str, "%Y-%m-%d")
        
        # Determine CLO based on strategy
        if clo_strategy == "manual":
            clo_val = manual_clo
        elif clo_strategy == "month":
            clo_val = calc.clo_by_month(date_obj)
        elif clo_strategy == "fixed_summer":
            clo_val = 0.5
        elif clo_strategy == "fixed_winter":
            clo_val = 1.0
        else:
            clo_val = calc.clo_fourier_4(date_obj)
            
        pmv_val, _ = calc.get_thermal_comfort_vba_base(
            ta=temp_val,
            rh=rh_val,
            vel=0.15,
            tr=temp_val,
            clo=clo_val,
            met=metabolic_rate
        )
        
        heatmap_data.append({
            "day": day_str,
            "pmv": round(pmv_val, 2)
        })

    return {"data": heatmap_data}


@app.get("/api/pmv-hourly-heatmap")
def get_pmv_hourly_heatmap(
    start_date: str | None = None,
    end_date: str | None = None,
    city: str | None = "beijing",
    dev_ids: list[str] | None = Query(None),
    clo_strategy: str = "fourier",
    manual_clo: float = 0.5,
    metabolic_rate: float = 1.0,
    db: Session = Depends(get_db),
):
    if start_date and end_date:
        try:
            start_obj = date.fromisoformat(start_date)
            end_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
    else:
        end_obj = date.today()
        start_obj = end_obj - timedelta(days=30) # Hourly view defaults to shorter range

    start_str = start_obj.isoformat()
    end_str = (end_obj + timedelta(days=1)).isoformat()

    # Base WHERE conditions
    where_conditions = [
        "create_time >= :start_date",
        "create_time < :end_date",
        "HOUR(create_time) BETWEEN 9 AND 18",
        "temp_num > 0",
        "rh_num > 0"
    ]
    query_params = {"start_date": start_str, "end_date": end_str}

    if dev_ids and len(dev_ids) > 0:
        where_conditions.append("dev_id IN :dev_ids")
        query_params["dev_ids"] = tuple(dev_ids)

    where_clause = " AND ".join(where_conditions)

    # Query hourly data for heatmap
    sql_query = text(f"""
        SELECT 
            DATE(create_time) AS day,
            HOUR(create_time) AS hour,
            AVG(temp_num) AS avg_temp,
            AVG(rh_num) AS avg_rh
        FROM environment_monitor
        WHERE {where_clause}
        GROUP BY day, hour
        ORDER BY day, hour
    """)

    try:
        results = db.execute(sql_query, query_params).fetchall()
    except Exception as e:
        print(f"Hourly query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    unique_days = sorted(list(set(str(row.day) for row in results)))
    day_to_idx = {d: i for i, d in enumerate(unique_days)}
    
    target_hours = list(range(9, 19))
    hour_to_idx = {h: i for i, h in enumerate(target_hours)}

    heatmap_data = []
    level_counts = {"level1": 0, "level2": 0, "level3": 0}
    total_count = 0

    for row in results:
        day_str = str(row.day)
        hour_val = int(row.hour)
        temp_val = float(row.avg_temp)
        rh_val = float(row.avg_rh)
        
        date_obj = datetime.strptime(day_str, "%Y-%m-%d")
        
        # Determine CLO based on strategy
        if clo_strategy == "manual":
            clo_val = manual_clo
        elif clo_strategy == "month":
            clo_val = calc.clo_by_month(date_obj)
        elif clo_strategy == "fixed_summer":
            clo_val = 0.5
        elif clo_strategy == "fixed_winter":
            clo_val = 1.0
        else:
            clo_val = calc.clo_fourier_4(date_obj)
            
        pmv_val, _ = calc.get_thermal_comfort_vba_base(
            ta=temp_val,
            rh=rh_val,
            vel=0.15,
            tr=temp_val,
            clo=clo_val,
            met=metabolic_rate
        )
        
        # Statistics
        total_count += 1
        abs_pmv = abs(pmv_val)
        if abs_pmv <= 0.5:
            level_counts["level1"] += 1
        elif abs_pmv <= 1.0:
            level_counts["level2"] += 1
        else:
            level_counts["level3"] += 1

        if day_str in day_to_idx and hour_val in hour_to_idx:
            heatmap_data.append([
                day_to_idx[day_str],
                hour_to_idx[hour_val],
                round(pmv_val, 2)
            ])

    stats = {
        "level1": round(level_counts["level1"] / total_count * 100, 1) if total_count > 0 else 0,
        "level2": round(level_counts["level2"] / total_count * 100, 1) if total_count > 0 else 0,
        "level3": round(level_counts["level3"] / total_count * 100, 1) if total_count > 0 else 0,
    }

    return {
        "days": unique_days,
        "hours": [f"{h:02d}:00" for h in target_hours],
        "data": heatmap_data,
        "stats": stats
    }


@app.get("/api/daily-trend")
def get_daily_trend(
    start_date: str | None = None,
    end_date: str | None = None,
    city: str | None = "beijing",
    dev_ids: list[str] | None = Query(None),
    clo_strategy: str = "fourier",
    manual_clo: float = 0.5,
    metabolic_rate: float = 1.0,
    db: Session = Depends(get_db),
):
    if start_date and end_date:
        try:
            start_obj = date.fromisoformat(start_date)
            end_obj = date.fromisoformat(end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format, expected YYYY-MM-DD")
    else:
        end_obj = date.today()
        start_obj = end_obj - timedelta(days=90)

    start_str = start_obj.isoformat()
    end_str = (end_obj + timedelta(days=1)).isoformat()

    # Base WHERE conditions
    where_conditions = [
        "create_time >= :start_date",
        "create_time < :end_date",
        "HOUR(create_time) BETWEEN 9 AND 18",
        "temp_num > 0",
        "rh_num > 0"
    ]
    query_params = {"start_date": start_str, "end_date": end_str}

    if dev_ids and len(dev_ids) > 0:
        where_conditions.append("dev_id IN :dev_ids")
        query_params["dev_ids"] = tuple(dev_ids)

    where_clause = " AND ".join(where_conditions)

    sql_query = text(f"""
        SELECT 
            DATE(create_time) AS day,
            AVG(temp_num) AS avg_temp,
            AVG(rh_num) AS avg_rh
        FROM environment_monitor
        WHERE {where_clause}
        GROUP BY day
        ORDER BY day
    """)

    try:
        results = db.execute(sql_query, query_params).fetchall()
    except Exception as e:
        print(f"Trend query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")

    data = []
    for row in results:
        day_value = row.day
        temp_value = float(row.avg_temp) if row.avg_temp is not None else None
        rh_value = float(row.avg_rh) if row.avg_rh is not None else None
        
        pmv_val = None
        clo_val = None
        
        if temp_value is not None and rh_value is not None:
            date_obj = datetime.combine(day_value, datetime.min.time()) if not isinstance(day_value, datetime) else day_value
            
            # Determine CLO based on strategy
            if clo_strategy == "manual":
                clo_val = manual_clo
            elif clo_strategy == "month":
                clo_val = calc.clo_by_month(date_obj)
            elif clo_strategy == "fixed_summer":
                clo_val = 0.5
            elif clo_strategy == "fixed_winter":
                clo_val = 1.0
            else:
                clo_val = calc.clo_fourier_4(date_obj)
                
            pmv_val, _ = calc.get_thermal_comfort_vba_base(
                ta=temp_value,
                rh=rh_value,
                vel=0.15,
                tr=temp_value,
                clo=clo_val,
                met=metabolic_rate
            )

        data.append({
            "day": str(day_value),
            "avg_temp": round(temp_value, 2) if temp_value else None,
            "avg_rh": round(rh_value, 1) if rh_value else None,
            "pmv": round(pmv_val, 2) if pmv_val else None,
            "clo": round(clo_val, 3) if clo_val else None
        })

    return {"data": data}


@app.post("/api/calculate-pmv", response_model=schemas.PMVResponse)
def calculate_pmv_endpoint(payload: schemas.PMVManualRequest):
    pmv_value, ppd_value = calc.get_thermal_comfort_vba_base(
        ta=payload.ta,
        rh=payload.rh,
        vel=payload.vel,
        tr=payload.tr,
        clo=payload.clo,
        met=payload.met,
    )

    return schemas.PMVResponse(
        pmv=round(pmv_value, 2),
        ppd=round(ppd_value, 1),
        clo=round(payload.clo, 2),
        ta=payload.ta,
        rh=payload.rh,
        vel=payload.vel,
    )
