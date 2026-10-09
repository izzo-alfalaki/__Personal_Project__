from common.connection.larkclient import LarkClient
from common.utility.bigqueryutility import BigQuery
from common.utility.larkutillitysdk import LarkSDK
from common.connection.gcpclient import GcpClient
from config.lark_report_table import *
import pandas as pd
import ast

class LarkPipelines:
    def __init__(self):
        self.Lark = LarkSDK( LarkClient, BASE_TOKEN, IZZO_TABLE )
        self.BigQuery = BigQuery( GcpClient().bq_client(), GcpClient().get_credits(), GcpClient.project_id )


    def lark_get_table_id( self ):
        response = self.Lark.ListTables()

        if response is None:
            return pd.DataFrame()  # []

        df = pd.json_normalize( response )

        # ids = df['table_id'].tolist()

        return df

    def get_table_from_bq( self ):
        self.BigQuery.push_query( 'call example.stored_procedure();' )
        df = self.BigQuery.query_to_dataframe( 'select * from Lark.Post_Table;' )

        return df 

    def lark_create_record_to_lark( self, df : pd.DataFrame, target_table = None, test_df = True ):
        if df.empty:
            return None

        if target_table is None:
            target_table =  'Post table'

        check_table_exists = [ c for c in df['name'].tolist() if target_table in c ]
        if not check_table_exists:
            raise ValueError(f'{target_table} not found.')
        
        mask = df['name'] == target_table 
        df = df.loc[mask]

        table_id = df['table_id'].tolist()[0]

        if test_df:
            test_data = { 'Text' : [ 'IJAT' , 'ROSNA' ], 'Record ID' : [ '', '' ] , 'Date' : [ '2001/04/06', '2001/04/12'] }
            test_data['Date'] = pd.to_datetime( test_data['Date'] )
            insert_data = pd.DataFrame( test_data )

        if not test_df:
            insert_data = self.get_table_from_bq()

        self.Lark.CreateRecords( insert_data , table_id)

    def full_bq_to_lark( self ):
        df = self.lark_get_table_id()
        self.lark_create_record_to_lark( df )

    def get_report_from_lark(self):
        res = self.Lark.SearchRecord()
        df = pd.json_normalize( res )
        print(df.info())

        for c in df.columns:
            if isinstance( df[c], str):
                try:
                    df[c] = ast.literal_eval( df[c] )
                except Exception as e:
                    print(e)

            df[c] = df[c].apply( lambda x: x[0] if (isinstance( x, list ) and x[0]) else x )
    
            try:
                df['file_token'] = df[c].apply( lambda x: x['file_token'] )
                df['url'] = df[c].apply( lambda x: x['url'] )
            except Exception as e:
                print(e)

            try:
                df['name_value'] = df[c].apply( lambda x: x['text'] )
            except Exception as e:
                print(e)

        for c in [c for c in df.columns if 'date' in c.lower()]:
            df[c] = pd.to_datetime( 
                        df[c], unit='ms', utc=True 
                        )#.dt.tz_convert('Asia/Kuala_Lumpur')

        df.columns = df.columns.str.replace( 'fields.', '' ).str.replace('.',  '_').str.lower()

        return df

    def send_report_to_bigquery(self, df ):
        self.BigQuery.df_to_bq( df, 'Lark', 'Table_Izzo', new=False )

    def full_lark_to_bq( self ):
        df = self.get_report_from_lark()
        self.send_report_to_bigquery(df)

    def update_report_in_lark( self ):
        """
        even better idea maybe 
         NOT TO USE: query.to_dataframe -> stimulate -> update, 
         
        but maybe use:
         SEARCH_RECORDS -> STIMULATE JSON / RESPONSE -> RESEND ( RE-SEND AS UPDATE RECORD )
        """
        # update table first
        strsql = self.BigQuery.get_procedure( 'lark', ['lark_table'] )
        self.BigQuery.push_query( strsql )

        # get record from bq
        query = """
        select 
         name.text as `name`, 
         number, multi_ops, 
         date as `Date`, 
         attachment.file_token as,  
         ...          
        from Lark.Table_Izzo_failappend;"""

        df = self.BigQuery.query_to_dataframe( query )
        record_id = df['record_id'].tolist()

        ## -- example stimulation
        df_edit = df.copy()
        df_edit['name'] = df_edit['name'].str.upper()  
        try:
            df_edit = df_edit.loc[ df_edit['record_id'] == record_id[0] ]
            self.Lark.UpdateRecordData( df_edit, record_id[0] )
        except Exception as e:
            print( e )
            pass

    def main( self ):
        self.full_lark_to_bq()
        self.full_bq_to_lark()