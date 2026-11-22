```python
from datetime import datetime, timedelta
from airflow.decorators import dag, task

from pipelines.genpipeline import GenerateBody, ETL, Runner


DEFAULT_ARGS = {
    "owner": "data-eng",
    "retries": 3,
    "retry_delay": timedelta(minutes=2),
}

@dag(
    dag_id="GeneratedData-Pipelines",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="30 6 * * *",
    catchup=False,
    max_active_runs=1
)
def generate_data_pipeline():
    @task
    def generate_and_load_mysql() -> str:
        runner = Runner()
        payload = GenerateBody(runner=runner).dump_all_data()

        etl = ETL(runner=runner)
        df = etl.get_response(payload)
        df_clean = etl.clean_response(df)
        etl.load_to_mysql(df_clean)

        return f"loaded {len(df_clean)} rows into MySQL"

    generate_and_load_mysql()


dag = generate_data_pipeline()
```