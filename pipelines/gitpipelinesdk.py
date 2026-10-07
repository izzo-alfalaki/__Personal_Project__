""" 
This pipeliens utilize the request methid of Lark, in other .py, we will demonstrate Lark SDK
"""
import ast
import pandas as pd

from common.connection.gcpclient import GcpClient
from common.connection.gitclient import GitClient
from common.connection.larkclient import LarkClient

from common.utility.gitutility import GitRequest
from common.utility.larkutillitysdk import LarkSDK
from common.utility.bigqueryutility import BigQuery

from pipelines.gitpipeline import GitPipelines

from config.lark_report_table import BASE_TOKEN as APP_TOKEN, IZZO_TABLE

class GitSDK:
    def __init__(self):
        self.Git = GitRequest(GitClient().declare())
        self.Lark = LarkSDK( LarkClient(), APP_TOKEN, IZZO_TABLE)
    
        gcp = GcpClient()
        self.BigQuery = BigQuery( gcp.bq_client(), gcp.get_credits(), gcp.project_id )

    def recall_workflow(self):
        workflow = GitPipelines()
        df = workflow.call_procedure()
        return df

    def send_report_to_lark(self, name = None):
        df = self.recall_workflow()
        try:
            self.Lark.UpdateRecordData( df )
        except Exception as e:
            print(e)

            if name is None:
                raise ValueError('no name assigned to new bit, break isntead')
            
            res = self.Lark.CreateBatchTable( name )
            if res is None:
                res = self.Lark.ListTables()
                
                dx = pd.json_normalize(res.get('items'))
                id = dx.loc[dx['name'] == name, 'table_id'].tolist()
                id = id[0] if id[0] else None

                self.Lark.table_id = id
                self.Lark.CreateRecords( df )

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

    def update_report_in_lark( self ):
        # get record from bq
        query = 'select * from Lark_table.lark; '

        df = self.BigQuery.query_to_dataframe( query )

        record_id = df['record_id'].tolist()

        # convert record to field format / payload
        df_edit = df.copy()

        ## -- example stimulation
        df_edit['given_name'] = df_edit['given_name'].str.upper()  

        for id in record_id:
            self.Lark.UpdateRecordData( df = df_edit, record_id = id )

    def main(self, send = False, get = False, update = False):
        if send:
            self.recall_workflow()
            self.send_report_to_lark()

        if get:
            df = self.get_report_from_lark()
            self.send_report_to_bigquery( df )

        if update:
            self.update_report_in_lark()


    