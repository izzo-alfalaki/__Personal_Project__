import numpy as np
import pandas as pd
#pd.set_option('display.max_columns', None)

from common.connection.gcpclient import GcpClient
from common.connection.gitclient import GitClient
from common.connection.larkclient import LarkClient

from common.utility.gitutility import GitRequest
from common.utility.larkutility import LarkRequests
from common.utility.bigqueryutility import BigQuery

class GitPipelines:
    def __init__(self):
        self.Git = GitRequest(GitClient().declare())
        self.Lark = LarkRequests( LarkClient().declare())
    
        gcp = GcpClient()
        self.BigQuery = BigQuery( gcp.bq_client(), gcp.get_credits(), gcp.project_id )

    def get_workflow_timing(self):
        data, id  = self.Git.get_runner_list()
        dx = pd.json_normalize( data )

        data = []
        for x in id:
            res = self.Git.get_run_timing( x )
            df = pd.json_normalize( res,
                                    record_path=['billable', 'UBUNTU', 'job_runs'],
                                    meta=[
                                          ['billable', 'UBUNTU', 'total_ms'],
                                          ['billable', 'UBUNTU', 'jobs'],
                                          'run_duration_ms' 
                                          ])
            df['id'] = x
            data.append( df )

        dy = pd.concat( data )

        xcol = ['id', 'name','run_number','created_at','updated_at','run_attempt','run_started_at','actor.type','triggering_actor.login','head_commit.author.email','repository.full_name','repository.owner.login' ]
        report = pd.merge( 
            dx[[ x for x in xcol if x in dx.columns  ]], 
            dy, on= 'id', how = 'left'  )

        datecol = [ x for x in report.columns if 'created' in x or 'updated' in x or 'started' in x]
        for c in datecol:
            report[c] = pd.to_datetime(report[c], utc=True).dt.tz_convert("Asia/Kuala_Lumpur")
        
        report['run_duration_ms'] = np.where( report['run_duration_ms'] > 0, report['run_duration_ms'] / 60000, report['run_duration_ms'] ) 
        report['retrived_date'] = pd.Timestamp.now().strftime( '%Y-%m-%d %H:%M:%S' ) 
        report = report.rename( columns = { 'billable.UBUNTU.jobs' : 'assigned_job_count'} )

        #report.to_parquet( 'actionrun_apipull.parquet' )
        
        return report #report.to_parquet( 'actionrun_apipull.parquet' )

    def load_to_bq(self, report):
        self.BigQuery.df_to_bq( report, 'Git', 'Actions', new=False )

    def push_procedure( self ) -> None:
        query = self.BigQuery.get_procedure('git', ['git_procedure'])
        query = query + ['call Git.aggregate(7);'] # to refresh current table if we update procedure

        for q in  query :
            try:
                job = self.BigQuery.client.query(q)
                job.result()
            except Exception as e:
                print(e)

    def call_procedure( self ):
        #before select from, must trigger procedure # tapi kay atas dah buat so yeah 
        df = self.BigQuery.query_to_dataframe( 'select * from Git_table.ActionsAggregate;'  ) 
        return df
    
    def send_report_to_lark(self):
        df = self.call_procedure()
        LARK_GIT_ID = 'example_ID'
        self.Lark.df_to_lark(  df, LARK_GIT_ID  )

    def main(self, update_procedure = False):
        df = self.get_workflow_timing()
        self.load_to_bq( df )

        if update_procedure:
            self.push_procedure()

        self.call_procedure()