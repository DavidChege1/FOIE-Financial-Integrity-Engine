from airflow import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

with DAG(
    dag_id='foie_financial_audit',
    start_date=datetime(2023, 1, 1),
    schedule_interval=None, 
    catchup=False,
    tags=['FOIE', 'Audit']
) as dag:

    # TASK 1: Prepare the Quarantine Environment
    # We ensure the schema and the flagging table exist before moving data.
    prepare_audit_env = PostgresOperator(
        task_id='prepare_audit_env',
        postgres_conn_id='postgres_default',
        sql="""
        CREATE SCHEMA IF NOT EXISTS stg_quarantine;
        CREATE SCHEMA IF NOT EXISTS fct_gold;

        CREATE TABLE IF NOT EXISTS stg_quarantine.orders_flagged (
            order_id TEXT,
            sku_code TEXT,
            quantity NUMERIC,
            unit_cost NUMERIC,
            supplier_id TEXT,
            timestamp TIMESTAMP,
            flag_reason TEXT,
            flagged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS fct_gold.audit_log (
            order_id TEXT,
            new_unit_cost NUMERIC,
            repaired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS fct_gold.orders_final (
            order_id TEXT,
            sku_code TEXT,
            quantity NUMERIC,
            unit_cost NUMERIC,
            supplier_id TEXT,
            timestamp TIMESTAMP,
            repaired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # TASK 2: The Integrity Gate
    # This logic identifies financial anomalies and moves them to Quarantine.
    # Note the use of '::' for explicit type casting to avoid DB errors.
    run_integrity_check = PostgresOperator(
        task_id='run_integrity_check',
        postgres_conn_id='postgres_default',
        sql="""
        -- 1. Move rows with Negative/Zero Costs or Missing Suppliers to Quarantine
        INSERT INTO stg_quarantine.orders_flagged (
            order_id, 
            sku_code, 
            quantity, 
            unit_cost, 
            supplier_id, 
            timestamp, 
            flag_reason
        )
        SELECT 
            order_id, 
            sku_code, 
            quantity::NUMERIC, 
            unit_cost::NUMERIC, 
            supplier_id, 
            timestamp::TIMESTAMP,
            'Financial Integrity Violation: Neg Cost or Null ID'
        FROM stg_raw.raw_orders
        WHERE unit_cost::NUMERIC <= 0 OR supplier_id IS NULL;

        -- 2. Remove those bad rows from the landing zone so they don't reach 'Gold'
        DELETE FROM stg_raw.raw_orders
        WHERE unit_cost::NUMERIC <= 0 OR supplier_id IS NULL;
        """
    )

    prepare_audit_env >> run_integrity_check
