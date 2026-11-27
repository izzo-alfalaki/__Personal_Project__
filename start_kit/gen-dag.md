```python

from datetime import datetime, timedelta
from airflow.decorators import dag, task

from pipelines.genpipeline import\
    Runner, GenerateBody, ETL, PostETL 


DEFAULT_ARGS = {
    "owner": "data-eng",
    "retries": 0,
    "retry_delay": timedelta(minutes=2),
}

@dag(
    dag_id="GeneratedData-Pipelines",
    default_args=DEFAULT_ARGS,
    start_date=datetime(2026, 1, 1),
    schedule="30 6 * * *",
    catchup=False,
    max_active_runs=1,
    tags = [ 'ETL Generated Data', 'BI Model Lift'  ]
)
def generate_data_pipeline():
    @task
    def etl() -> str:
        runner = Runner()
        payload = GenerateBody(runner=runner).dump_all_data()

        etl = ETL(runner=runner)
        df = etl.get_response(payload)
        df_clean = etl.clean_response(df)
        etl.load_to_mysql(df_clean)

        return f"ETL : loaded {len(df_clean)} rows into MySQL"

    @task
    def post_etl( etl_status : str  ) -> str:
        runner = Runner()
        postetl = PostETL( runner )

        df = postetl.from_mysql()
        mysql_bq_status = postetl.to_bigquery( df )

        appendix_transfer = postetl.push_appendix()
        
        return f""" {etl_status } -->
                    | 
                    PosETL Log: 
                    From MySQL[{len(df)}] ->   
                    {mysql_bq_status} ->
                    {appendix_transfer}"""

    etl_status = etl()
    post_etl( etl_status  )

dag = generate_data_pipeline()

```