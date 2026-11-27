from common.connection.larkclient import LarkClient
from common.utility.bigqueryutility import BigQuery

from common.utility.larkutillitysdk import LarkSDK
from common.connection.gcpclient import GcpClient

from config.lark_report_table import *

from common.utility.mysqlutility import MySQL
from common.connection.mysql import MysqlClient

import pandas as pd
import ast

class Runner:
    def __init__(self, local = False ):
        self.Lark = LarkSDK( client=LarkClient, app_token=BASE_TOKEN, report = EMPLOYEE )
        
        if not local:
            client= MysqlClient().engine(  user_package = 'izzo', database = 'raw' )
        if local:
            client = MysqlClient().retry_engine(  user_package = 'izzo', database = 'raw' )
        self.mysql = MySQL( client ) 
        
        self.BigQuery = BigQuery( GcpClient().bq_client(), GcpClient().get_credits(), GcpClient().project_id )

    def lark_get_table_list( self ):
        response = self.Lark.ListTables()

        if response is None:
            return pd.DataFrame()  # []

        df = pd.json_normalize( response )

        # ids = df['table_id'].tolist()

        return df

class ETL:
    def __init__(self, runner):
        self.runner = runner or Runner()

    def general_standard_clean( self, df : pd.DataFrame ) -> pd.DataFrame:
        minus = df.select_dtypes(include=["number", "object"]).columns.tolist()
        for c in [ c for c in df.columns.tolist() if c not in minus ]:
            try:
                df[c] = df[c].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
            except Exception as e:
                print( e )
                pass

        for c in [ c for c in df.columns.tolist() ]:
            try:          
                df[c] = df[c].apply( lambda x: x[0]['text'] if x[0]['text'] else x )
            except Exception as e:
                print( e )
                pass
            
        for c in [c for c in df.columns if 'date' in c.lower()]:
            
            df[c] = df[c].apply(lambda x: x[0] if isinstance(x, list) and len(x) > 0 else x)
            
            df[c] = pd.to_datetime( 
                        df[c], unit='ms', utc=True, errors='coerce' 
                            ).dt.tz_convert('Asia/Kuala_Lumpur')

        df.columns = df.columns.str.replace( 'fields.', '' ).str.replace('.',  '_').str.lower()
        use_col = [  c for c in df.columns if 'type' not in c.lower() ]
        df = df[ use_col ]

        return df

    def clean_schedule( self, df : pd.DataFrame ) -> pd.DataFrame:
        to_list_cols = ['cashier', 'receptionist', 'store operator', 'general support', 'supervisor', 
                        'supporting cashier', 'supporting receptionist', 'supporting store']

        df['all_on_duty'] =  [[] for _ in range(len(df))]
        for col in to_list_cols:
            df[ col ] = df[col].apply( 
                lambda x : ast.literal_eval(x) if isinstance( x, str ) and x is not None else x )

            df['all_on_duty'] = df['all_on_duty'] + df[col].apply( lambda x: x if not isinstance( x, float) else []) 


        df['supervisor'] = df['supervisor'].apply( lambda x : x[0] if not isinstance( x, float ) else pd.NA )

        df[ 'total_incharge' ] = df[ 'all_on_duty' ].apply( lambda x : len(x) if isinstance(x, list) else 0)
        return df

    def get_df_from_table_id(self, **kwargs):
        res = self.runner.Lark.SearchRecord( **kwargs )
        if res is None:
            return pd.DataFrame()

        # for local test
        # import json
        # with open("inspect.json", "w", encoding="utf-8") as f:       
        #     json.dump(res, f, indent=4)
        
        initdf = pd.json_normalize( res )

        if initdf.empty  or len( initdf ) <= 1:
            return pd.DataFrame()
        
        print(f'PRE: checking extract reponse: {len(initdf)}')

        df = self.general_standard_clean(initdf)
        print(f'POST: checking extract reponse: {len(df)}')

        return df

    def extract( self, production : bool = True ):
        df = self.runner.lark_get_table_list()
        if df.empty:
            raise ValueError('No tables found in LarkBase.')

        if not production:
            df.to_csv( 'list_of_tables.csv', index=False )

        table_list_result = zip( df['name'].unique().tolist(), df['table_id'].unique().tolist() )
        
        fetch_df_results = {}
        for key, id in table_list_result:
            fetch_df = self.get_df_from_table_id( new_table_id = id )
            fetch_df_results[ key ] = fetch_df

        return list(table_list_result), fetch_df_results

    def transform( self, fetch_df_results : dict, production = True ):    
        transform_tables = {}
        transform_results = {}
        
        for key, df in fetch_df_results.items():
            
            df : pd.DataFrame
            
            if df.empty:
                transform_tables[key] =  f"{key} : Null - pd.DataFrame()"
                continue

            if not production:
                df.to_csv( f"raw_{str(key).lower().replace(' ', '_')}_table.csv", index=False )

            if key == 'Schedule':
                df = self.clean_schedule( df )
            else:
                print( f'{key}: not assigned post clean' )

            transform_tables[key] =  f"{key} : {len( df )}"
            transform_results[ key ] = df

        return transform_tables, transform_results

    def load( self, transform_results : dict, production = True,  ):
        """
        pulled from API, so raw data, for mysql
        """
        load_results = {}
        for key, df in transform_results.items():    
            if production:
                clean_name = str(key).lower().replace(' ', '_')

                df : pd.DataFrame
                
                if df is None or df.empty:
                    load_results[ clean_name ] =  f'null df, empty df at stage Upload to MySQL'
                    continue
        
                try:
                    self.runner.mysql.load_df_to_table( df , clean_name , if_exists='append' )
                    load_results[ clean_name ] = f" {clean_name} : appended to mysql"
                except:
                    for c in df.columns:
                        df[c] = df[c].astype( str )

                    try:
                        new_name = f"{ clean_name }_failed_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
                        self.runner.mysql.load_df_to_table( df , new_name , if_exists='replace' )
                        load_results[ clean_name ] = f"{clean_name} : failed to upload as - {new_name}"
                    except Exception as e:
                        print( e )
                        load_results[ clean_name ] = f"{clean_name} : disturbed at retry-upload stage {e}"
                        pass
            else:
                clean_name = str(key).lower().replace(' ', '_')
                df.to_csv( f"mysql_{clean_name}_table.csv", index=False )
                load_results[ clean_name ] = 'table was saved as csv instead, not cloud testing.'
                
        return load_results 

class PostETL:
    def __init__(self, runner):
        self.runner = runner or Runner()

    def from_mysql( self ):
        query = [
            """ 
            with a as(
            select record_id, category, column_position, id, item_name, price, rack_value, row_position, cast( left( unique_timestamp, 19 ) as datetime ) as unique_timestamp 
            from racks
            )
            ,b as (
            SELECT 
                *, ROW_NUMBER() over ( PARTITION BY record_id ORDER BY unique_timestamp desc ) as rn  
            FROM a  
            )

            select * from b where rn = 1;
            """,
            """
            with a as(
            SELECT 
                *, ROW_NUMBER() over ( PARTITION BY record_id ORDER BY 
                                        cast( left(unique_timestamp, 19) as DATETIME) 
                                        desc ) as rn
            FROM `schedule`
            )

            select * from a where rn = 1;
            """
        ]
        
        xcom = {}
        results = {}
        for key, q in zip( [ 'rack', 'schedule' ]  , query  ):
            try:
                df = self.runner.mysql.query_to_df( q )
                xcom[ key ] = f'query success: { len( df ) }'
                results[ key ] = df

            except Exception as e:
                xcom[ key ] = f'query results : {e}'
                results[ key ] = pd.DataFrame()

        return xcom, results

    def to_bq( self, results : dict ):

        xcom = {}
        for key, df in results.items():
            to_list_cols = ['cashier', 'receptionist', 'store_operator', 'general_support', 'supervisor', 
                            'supporting_cashier', 'supporting_receptionist', 'supporting_store', 'all_on_duty']
            try:
                new_name = str(key).title()
                self.runner.BigQuery.df_to_bq( df, 'Lark', new_name, new = True, list_exists= to_list_cols )
                xcom[ key ] = f'loaded to bq as {new_name} : {len(df)}'
            except Exception as e:
                xcom[ key ] = f'fail to load {key} : {e}'

        return xcom

    def trigger_procedure( self ):
        trigger_results = {}
        query = 'call Lark.model();'
        try:
            job = self.runner.BigQuery.client.query( query )
            job.result()
            trigger_results[ query ] = f" success : { job.job_id } "
        except Exception as e:
            trigger_results[ query ] = str(e)
        
        return trigger_results

#########################################################################################################################
# -------------------------------------------- BREAK OF SIGNIFICANT METHOD -------------------------------------------- #
#########################################################################################################################
class LarkReportStage:
    def __init__(self, runner ):
        self.runner = runner or Runner()
    
    def mysql_to_bq( self ):
        ql = [
            """
                select * from employee_table 
                qualify ROW_NUMBER() over ( 
                    partition by record order by CAST(
                        left(unique_timestamp, 18) as DATETIME
                    ) DESC ) = 1 ; 

            """
            ,
            """
            select * from salary_table
                qualify ROW_NUMBER() over ( 
                partition by record_id, qualified_position order by CAST(
                    left(unique_timestamp, 18) as DATETIME
                ) DESC ) = 1;
            """
            ]

        xcom_list = []
        for x, q in zip( [ 'employee_table', 'salary_table' ], ql ) :
            try:
                df = self.runner.mysql.query_to_df( q )
        
                if df is None:
                    print(f'skipping for : {x} - NoneType')
                    xcom_list.append( f'fail {x}' )
                    continue
                if df.empty:
                    print(f'skipping for : {x} - pd.DataFrame')
                    xcom_list.append( f'fail {x}' )
                    continue            

                self.runner.BigQuery.df_to_bq( df, 'Lark', x.title().split('_')[0], new = True)

                xcom_list.append( x )

            except Exception as e:
                print( f'decide the stage error: {e}' )
                xcom_list.append( f'fail {x}')
                pass

    def get_table_from_db( self ):
        #- pulling data from report always agg-level, so from bq
        #if not bigquery:
        #    self.mysql.execute_statement( 'call stored_procedure();' )
        #    self.mysql.query_to_df( 'select * from Post_Table;')

        self.runner.BigQuery.push_query( 'call example.stored_procedure();' )
        df = self.runner.BigQuery.query_to_dataframe( 'select * from Lark_table.modeled_employee;' )

        return df 

    def create_record_to_lark( self, appendix : pd.DataFrame, target_table : str, test_df = True ):        
        mask = appendix['name'] == target_table 
        appendix = appendix.loc[mask]
        table_id = appendix['table_id'].tolist()[0]

        if test_df:
            test_data = { 'Text' : [ 'izzo' ], 'Record ID' : [ '' ] , 'Date' : [ '2001/06/27'] }
            test_data['Date'] = pd.to_datetime( test_data['Date'] )
            insert_data = pd.DataFrame( test_data )

        if not test_df:
            insert_data = self.get_table_from_db()

        self.runner.Lark.CreateRecords( insert_data , table_id)

    def full_db_to_lark( self , target_table : str ):
        df_appendix = self.runner.lark_get_table_list()
        appendix = df_appendix['name'].tolist()
        new_name = target_table

        check_table_exists = [ val for val in appendix if target_table in val ]
        if df_appendix.empty:
            print( 'WARNING: appendix retuurn pd.DataFrame(), force create table')
        elif not check_table_exists:     
            print( 'no name in appendix found, force create table')
                
            res = self.runner.Lark.CreateBatchTable( new_name )
            if isinstance( res , dict):
                pass
            else:
                ast.literal_eval( res )

            aidee = res.get('table_ids')
            aidee = aidee[0] if isinstance( aidee, list) and len( aidee ) <= 1 else aidee

            df_appendix.loc[ len( df_appendix )] = { "table_id": aidee, "name": new_name }

        self.create_record_to_lark( df_appendix, new_name, False  )

    def update_report_in_lark( self ):
        """
        even better idea maybe 
         NOT TO USE: query.to_dataframe -> stimulate -> update (* IF ERROR), 
         
        but maybe use:
         SEARCH_RECORDS -> STIMULATE JSON / RESPONSE -> RESEND ( RE-SEND AS UPDATE RECORD )
        """
        # update table first
        strsql = self.runner.BigQuery.get_procedure( 'lark', ['lark_table'] )
        self.runner.BigQuery.push_query( strsql )

        # get record from bq
        query = """
        select 
         name.text as `name`, 
         number, multi_ops, 
         date as `Date`, 
         attachment.file_token as,  
         ...          
        from Lark.Table_Izzo_failappend;"""

        df = self.runner.BigQuery.query_to_dataframe( query )
        record_id = df['record_id'].tolist()

        ## -- example stimulation
        df_edit = df.copy()
        df_edit['name'] = df_edit['name'].str.upper()  
        try:
            df_edit = df_edit.loc[ df_edit['record_id'] == record_id[0] ]
            self.runner.Lark.UpdateRecordData( df_edit, record_id[0] )
        except Exception as e:
            print( e )
            pass