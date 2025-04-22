from fastapi import APIRouter
import sqlite3
from typing import List
from pydantic import BaseModel

router = APIRouter()

class MetricSummary(BaseModel):
    function_id: int
    backend: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    min_time: float
    max_time: float
    avg_time: float

@router.get("/metrics", response_model=List[MetricSummary])
def get_metrics():
    conn = sqlite3.connect("lambda_platform.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            function_id,
            backend_used,
            COUNT(*) as total_runs,
            SUM(success) as successful_runs,
            COUNT(*) - SUM(success) as failed_runs,
            MIN(duration),
            MAX(duration),
            AVG(duration)
        FROM execution_metrics
        GROUP BY function_id, backend_used
    """)
    
    results = cursor.fetchall()
    conn.close()

    return [
        MetricSummary(
            function_id=row[0],
            backend=row[1],
            total_runs=row[2],
            successful_runs=row[3],
            failed_runs=row[4],
            min_time=round(row[5], 3) if row[5] else 0.0,
            max_time=round(row[6], 3) if row[6] else 0.0,
            avg_time=round(row[7], 3) if row[7] else 0.0,
        )
        for row in results
    ]
