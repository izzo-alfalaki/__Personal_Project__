from pipelines.genpipeline import *

def genmain():
    runner = Runner( local = True )
    payload = GenerateBody(runner=runner).dump_all_data()

    etl = ETL(runner=runner)
    df = etl.get_response(payload)
    df_clean = etl.clean_response(df)
    etl.load_to_mysql(df_clean)

    post_etl = PostETL( runner )
    df = post_etl.from_mysql()
    post_etl.to_bigquery( df )

    push_appendix_status\
    = post_etl.push_appendix()

    if push_appendix_status:
        final_pipelines_results = post_etl.push_procedure()

    print( final_pipelines_results )

def schema():
    GenSchema()
    with open( 'config/appendix.json' , 'r' ) as x:
        data = json.load( x )

    df = pd.json_normalize(data.get( 'res' )) 

    from common.connection.mysql import MysqlClient
    from common.utility.mysqlutility import MySQL

    mysql = MySQL( MysqlClient().retry_engine( user_package = 'izzo', database = 'raw' ) )
    mysql.load_df_to_table( df , 'gen_appendix', if_exists="replace")

    from common.connection.gcpclient import GcpClient
    from common.utility.bigqueryutility import  BigQuery

    gcp = BigQuery( GcpClient().bq_client(), GcpClient().get_credits(), GcpClient().project_id )
    gcp.df_to_bq( df, 'Gen', 'Appendix', True )

if __name__ == '__main__':
    genmain()