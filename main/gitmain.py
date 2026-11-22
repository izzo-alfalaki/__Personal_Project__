from pipelines.gitpipeline import ETL, PostETL

if __name__ == '__main__':
    etl = ETL()
    df = etl.etl()
    post_etl = PostETL()
    df = post_etl.post_etl()
    #PostETL().send_report_to_lark()