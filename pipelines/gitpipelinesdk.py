""" 
This pipeliens utilize the request methid of Lark, in other .py, we will demonstrate Lark SDK
"""
import pandas as pd

from common.connection.gcpclient import GcpClient
from common.connection.gitclient import GitClient
from common.connection.larkclient import LarkClient

from common.utility.gitutility import GitRequest
from common.utility.larkutillitysdk import LarkSDK
from common.utility.bigqueryutility import BigQuery

from pipelines.gitpipeline import GitPipelines

from config.lark_report_table import BASE_TOKEN as APP_TOKEN, GIT_REPORT

class GitSDK:
    def __init__(self):
        self.Git = GitRequest(GitClient().declare())
        self.Lark = LarkSDK( LarkClient, APP_TOKEN, GIT_REPORT)
    
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

    def main(self):
        self.recall_workflow()
        self.send_report_to_lark()