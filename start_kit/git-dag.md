```python

from datetime import datetime, timedelta
from airflow.decorators import dag, task

from pipelines.gitpipeline import ETL, PostETL


DEFAULT_ARGS = {
    "owner": "data-eng",
    "retries": 0,
    "retry_delay": timedelta(minutes=2)
}

@dag(
    dag_id="Git-ETLPipelines",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="30 6 * * *",
    catchup=False,
    max_active_runs=1,
    tags=["etl", "bi_model"],
)
def git_actions_etl():
    @task
    def etl() -> str:
        etl = ETL()
        df = etl.etl()
        return f"fetched df status: rows={len(df) if df is not None else 0}"

    @task
    def postetl(extract_status: str) -> str:
        post_etl = PostETL()
        df = post_etl.post_etl()
        return f"{extract_status} -> Model in BigQuery Status : {len(df) if df is not None else 0}"

    etl_status = etl()
    #mysql_to_bq(etl_status)

dag = git_actions_etl()
```