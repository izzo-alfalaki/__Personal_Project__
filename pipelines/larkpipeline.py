from common.connection.larkclient import LarkClient
from common.utility.bigqueryutility import BigQuery

from common.utility.larkutillitysdk import LarkSDK
from common.connection.gcpclient import GcpClient

from config.lark_report_table import *

from common.utility.mysqlutility import MySQL
from common.connection.mysql import MysqlClient

import pandas as pd
import ast

class LarkPipelines:
    def __init__(self):
        self.Lark = LarkSDK( client=LarkClient, app_token=BASE_TOKEN, report = EMPLOYEE )
        self.mysql = MySQL( client= MysqlClient().engine(  user_package = 'izzo', database = 'raw' )) 
        self.BigQuery = BigQuery( GcpClient().bq_client(), GcpClient().get_credits(), GcpClient().project_id )

    def lark_get_table_list( self ):
        response = self.Lark.ListTables()

        if response is None:
            return pd.DataFrame()  # []

        df = pd.json_normalize( response )

        # ids = df['table_id'].tolist()

        return df

class ETL:
    def __init__(self):
        self.runner = LarkPipelines()

    def general_standard_clean( self, df : pd.DataFrame ) -> pd.DataFrame:
        minus = df.select_dtypes(include= [ 'float', 'int', 'str'] ).columns.tolist()
        for c in [ c for c in df.columns.tolist() if c not in minus ]:
            df[c] = df[c].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        
            try:          
                df[c] = df[c].apply( lambda x: x[0]['text'] if x[0]['text'] else x )
            except:
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

    def clean_employee_table( self, df : pd.DataFrame ) -> pd.DataFrame:
        
        num_cols_need_clean = [  
                'age_value' , 'available leave this year_value' , 'contract left ( month )_value' , 'loyalty payout_value' , 'requestabe annual leave_value' , 'resign notice ( days )_value' , 'cummulative performance_value'
            ]

        for c in num_cols_need_clean:
            #df[c] = df[c].apply(lambda x: x[0] if not isinstance(x, [ float | int]) and len(x) > 0 else x)
            df[c] = df[c].apply(lambda x: x if isinstance( x , float) or isinstance( x, int) or isinstance( x, str) else x[0])
            df[c] = pd.to_numeric( df[c], errors = 'coerce')
            df[c] = df[c].fillna(0)

        df.columns = df.columns.str.split( '_' ).str[0]
        return df

    def clean_salary_table( self, df : pd.DataFrame, production : bool = True ) -> pd.DataFrame:
        for x in [ 'qualified position', 'base bonus_value', 'base pay_value']:  
            df[x] = df[x].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
            if not x == 'qualified position':
                df[x] = df[x].apply(lambda x: x[0] if len(x) <= 1 else x)

        if production:
            if 'qualified position' in df.columns:
                df = df.explode('qualified position')
            else:
                print('WARNING: qualified position column not found in dataframe')
        
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

    def full_lark_to_db( self, production : bool = True ):
        df = self.runner.lark_get_table_list()
        if df.empty:
            raise ValueError('No tables found in LarkBase.')

        if not production:
            df.to_csv( 'list_of_tables.csv', index=False )

        manual_key = [ 'Employee Table', 'Salary Table' ]
        test_table_id = [ df['table_id'].tolist()[0], df['table_id'].tolist()[1]]
    
        zip_package = zip( df['name'].unique().tolist(), df['table_id'].unique().tolist() )
        
        tables = {}
        for key, id in zip_package if production else zip( manual_key, test_table_id ):
            fetch_df = self.get_df_from_table_id( new_table_id = id )

            if fetch_df.empty:
                continue

            if not production:
                fetch_df.to_csv( f"raw_{key.lower().replace(' ', '_')}_table.csv", index=False )

            if key == 'Employee Table':
                fetch_df = self.clean_employee_table( fetch_df )
            elif key == 'Salary Table':
                fetch_df = self.clean_salary_table( fetch_df )
            else:
                print( f'{key}: not assigned post clean' )
            
            tables[key] = fetch_df

            if production:
                try:
                    # this is stage data, so we dont sell to bq, preserved for agg
                    # self.BigQuery.df_to_bq( df, 'Lark', clean_name, new=False )                     

                    clean_name = key.lower().replace(' ', '_')
                    self.runner.mysql.load_df_to_table(
                        fetch_df, clean_name, if_exists='append'
                        ) 
                
                except Exception as e:
                    print(e)
                    pass
            else:
                fetch_df.to_csv( f"mysql_{clean_name}_table.csv", index=False )

class PostETL:
    def __init__(self):
        self.runner = LarkPipelines()

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
        
        for x, q in zip( [ 'employee_table', 'salary_table' ], ql ) :
            try:
                df = self.runner.mysql.query_to_df( q )
        
                if df is None:
                    raise ValueError( 'df is NoneType' )
                if df.empty:
                    raise ValueError( 'df is Empty' )            

                self.runner.BigQuery.df_to_bq( df, 'Lark', x.title().split('_')[0], new = True)

            except Exception as e:
                print( f'decide the stage error: {e}' )
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