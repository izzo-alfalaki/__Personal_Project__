```python

from datetime import datetime, timedelta
from airflow.decorators import dag, task

from pipelines.larkpipeline import ETL, PostETL, Runner


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
    tags = [ 'ETL All Lark Base Table', 'BI Model All']
)
def lark_pipeline():
    @task
    def etl() -> str:
        runner = Runner()

        etl = ETL( runner )
        
        etl_info, fetched_df = etl.extract()
        transform_info, transform_results = etl.transform( fetched_df )
        load_info = etl.load( transform_results )
        
        return f"""etl_info : { ','.join(etl_info)}  --> 
        transform_info : {transform_info} --> load_info : {load_info}"""

    @task
    def postetl( etl_status: str = None) -> str:
        runner = Runner()

        postetl = PostETL( runner )
        mysql_info, mysql_pulled = postetl.from_mysql()
        bq_info = postetl.to_bq( mysql_pulled )
        
        trigger_info = postetl.trigger_procedure()


        postetl_status = f"PostETL Status : From-mysql - {mysql_info } --> To BQ - {bq_info} --> Trigger Procedure - { trigger_info }" 
        if etl_status:
            return f"ETL-Status: {etl_status} --> PostETL-Status : {postetl_status}"

        else:
            return postetl_status

    etl_status = etl()
    postetl(etl_status)

dag = lark_pipeline()
```