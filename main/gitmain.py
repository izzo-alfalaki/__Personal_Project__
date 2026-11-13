from pipelines.gitpipeline import ETL, PostETL

if __name__ == '__main__':
    ETL().etl()
    PostETL().send_report_to_lark()