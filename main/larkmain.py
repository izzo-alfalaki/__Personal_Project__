from pipelines.larkpipelines import ETL, PostETL

if __name__ == '__main__':
    ETL().full_lark_to_db()
    PostETL().full_db_to_lark()