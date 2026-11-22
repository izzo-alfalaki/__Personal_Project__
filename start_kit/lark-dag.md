```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task

from pipelines.larkpipeline import ETL, PostETL


DEFAULT_ARGS = {
    "owner": "data-eng",
    "retries": 0,
    "retry_delay": timedelta(minutes=2)
}

@dag(
    dag_id="Lark-ETLPipelines",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="30 6 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["lark", "etl"],
)
def lark_pipelines():
    @task
    def extract_transform_load_lark() -> str:
        etl = ETL()
        tables = etl.etl( production=True)
        return f"fetch_tables : { ' , '.join([c for c in tables.keys()] )   }"

    @task
    def load_lark_to_bq(extract_status: str) -> str:
        etl = PostETL()
        xcom_list = etl.mysql_to_bq()
        return f"{extract_status} -> To-BigQuery status: { ' , '.join( xcom_list )}"

    #status = extract_transform_load_lark()
    #load_lark_to_bq(status)

    extract_transform_load_lark()

dag = lark_pipelines()
```