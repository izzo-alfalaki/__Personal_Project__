from pipelines.genpipeline import *

if __name__ == '__main__':
    runner = Runner()
    payload = GenerateBody(runner=runner).dump_all_data()

    etl = ETL(runner=runner)
    df = etl.get_response(payload)
    df_clean = etl.clean_response(df)
    etl.load_to_mysql(df_clean)