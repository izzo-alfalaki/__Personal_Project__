from pipelines.larkpipeline import ETL, PostETL

if __name__ == '__main__':
    etl = ETL()
    tables = etl.etl( production=True)
    #etl = PostETL()
    #etl.mysql_to_bq()