```python

from datetime import datetime, timedelta
from airflow.decorators import dag, task

from pipelines.gitpipeline import ETL, PostETL, Runner


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
    tags = [ 'ETL Git Actions', 'BI Model Workflow Runs'  ]
)
def git_actions_pipeline():
    @task
    def etl() -> str:
        runner = Runner()
        etl = ETL( runner)
        
        df = etl.etl()
        return f"fetched df status: rows={len(df) if df is not None else 0}"

    @task
    def postetl(extract_status: str) -> str:
        runner = Runner() 
        post_etl = PostETL( runner )
        
        df = post_etl.from_mysql()
        status = post_etl.to_bigquery( df )
        procedure_echo = post_etl.push_procedure()

        return \
        f"""
        ETL status : {extract_status} 
        -> MySQL <> BigQuery Status : {status}-{len(df) if df is not None else 0} 
        -> Model (Procedure) Status : {procedure_echo}
        """

    etl_status = ""
    etl_status = etl()
    postetl(etl_status)

dag = git_actions_pipeline()
```