from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2.extras import RealDictCursor
from pydantic import BaseModel
import os

app = FastAPI(title="FOIE Financial Integrity API")

DB_CONFIG = {
    "host": os.environ.get("POSTGRES_HOST", "postgres"),
    "database": os.environ.get("POSTGRES_DB", "foie_db"),
    "user": os.environ.get("POSTGRES_USER", "airflow"),
    "password": os.environ.get("POSTGRES_PASSWORD", "airflow"),
    "port": int(os.environ.get("POSTGRES_PORT", 5432))
}

class RepairRequest(BaseModel):
    order_id: str
    new_unit_cost: float

@app.get("/quarantine")
def get_quarantine():
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("SELECT * FROM stg_quarantine.orders_flagged;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {"flagged_count": len(rows), "data": rows}

@app.post("/repair")
def repair_order(request: RepairRequest):
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        # 1. Move to Gold Table with corrected price
        cur.execute("""
            INSERT INTO fct_gold.orders_final (order_id, sku_code, quantity, unit_cost, supplier_id, timestamp)
            SELECT order_id, sku_code, quantity, %s, COALESCE(supplier_id, 'REPAIRED'), timestamp
            FROM stg_quarantine.orders_flagged
            WHERE order_id = %s;
        """, (request.new_unit_cost, request.order_id))
        
        # 2. Remove from Quarantine
        cur.execute("DELETE FROM stg_quarantine.orders_flagged WHERE order_id = %s;", (request.order_id,))
        
        conn.commit()
        return {"status": "success", "message": f"Order {request.order_id} repaired and moved to Gold table."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()