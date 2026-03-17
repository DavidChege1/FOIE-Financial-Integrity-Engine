from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from datetime import datetime

# Function to handle the CSV to Postgres ingestion
def load_csv_to_postgres():
    from airflow.providers.postgres.hooks.postgres import PostgresHook
    import pandas as pd
    import os

    # 1. Get connection details from Airflow
    # This assumes you have set up 'postgres_default' in the UI
    hook = PostgresHook(postgres_conn_id='postgres_default')
    conn = hook.get_connection('postgres_default')
    
    # 2. Build a clean SQLAlchemy URI manually to bypass the "__extra__" bug
    user = conn.login
    password = conn.password
    host = conn.host
    port = conn.port or 5432
    dbname = conn.schema
    
    db_uri = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    
    # 3. Define File Path (Relative to the container's mount)
    file_path = '/opt/airflow/dags/data/raw_erp_dump.csv'
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The ERP dump was not found at {file_path}. Did you run the generator script?")

    # 4. Load the data using Pandas
    df = pd.read_csv(file_path)
    
    # 5. Push to Postgres (Replace existing data in the staging landing zone)
    df.to_sql('raw_orders', db_uri, schema='stg_raw', if_exists='replace', index=False)
    print("✅ Successfully ingested ERP data into stg_raw.raw_orders")

# DAG Definition
with DAG(
    dag_id='foie_erp_ingestion',
    start_date=datetime(2023, 1, 1),
    schedule_interval='@daily',
    catchup=False,
    tags=['FOIE', 'Ingestion']
) as dag:

    # Task 1: Ensure the staging schema exists
    create_schema_task = PostgresOperator(
        task_id='create_schema_if_missing',
        postgres_conn_id='postgres_default',
        sql="CREATE SCHEMA IF NOT EXISTS stg_raw;"
    )

    # Task 2: Execute the Python ingestion
    ingest_data_task = PythonOperator(
        task_id='ingest_csv_to_postgres',
        python_callable=load_csv_to_postgres
    )

    # Set dependency
    create_schema_task >> ingest_data_task
