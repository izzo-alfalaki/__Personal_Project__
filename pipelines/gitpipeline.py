""" 
This pipeliens utilize the request methid of Lark, in other .py, we will demonstrate Lark SDK
"""
import ast
import numpy as np
import pandas as pd

from common.connection.gcpclient import GcpClient
from common.connection.gitclient import GitClient
from common.connection.larkclient import LarkClient
from common.connection.mysql import MysqlClient

from common.utility.gitutility import GitRequest
from common.utility.larkutility import LarkRequests
from common.utility.bigqueryutility import BigQuery
from common.utility.mysqlutility import MySQL

from config.lark_report_table import BASE_TOKEN as APP_TOKEN, GIT_REPORT

class GitPipelines:
    def __init__(self):
        self.Git = GitRequest(GitClient().declare())
        self.Lark = LarkRequests( LarkClient().declare(), APP_TOKEN)
    
        gcp = GcpClient()
        self.BigQuery = BigQuery( gcp.bq_client(), gcp.get_credits(), gcp.project_id )
        self.mysql = MySQL( client= MysqlClient().engine(  user_package = 'izzo', database = 'raw' ))

        self.table_id = GIT_REPORT.get('TABLE_ID')
        self.report_name = 'git_actions'

class ETL:
    """
    ###################################################################
                            ## ETL ##
    ###################################################################
    """    
    def __init__(self):
        self.runner = GitPipelines()

    def inloop_clean(self, df : pd.DataFrame ):
        if df is None or df.empty:
            return pd.DataFrame()
        
        df['billable.UBUNTU.job_runs'] = \
        df['billable.UBUNTU.job_runs'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        df.explode('billable.UBUNTU.job_runs', ignore_index=True)

        df['job_id'] = df['billable.UBUNTU.job_runs'].apply( 
            lambda x : x[0].get( 'job_id') if x[0] else None
            ) 

        df['job_id_duration_ms'] = df['billable.UBUNTU.job_runs'].apply( 
            lambda x : x[0].get( 'duration_ms') if x[0] else None
            )

        return df

    def clean_all( self, dx : pd.DataFrame , dy : pd.DataFrame ):
            if dx is None or dx.empty:
                return pd.DataFrame()
            
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

    def get_workflow_timing(self ) -> pd.DataFrame:
        res  = self.runner.Git.get_runner_list()

        if not res[0].get('workflow_runs'):
            print('nop workflow run found')
            return pd.DataFrame()
        else:
            dx = pd.json_normalize( res[0].get('workflow_runs') )    
            id_list = dx['id'].tolist()                

        data = []
        for x in id_list:
            res = self.runner.Git.get_run_timing( x )

            if not res:
                continue

            df = pd.json_normalize( res
                                    #, record_path=['billable', 'UBUNTU', 'job_runs'],
                                    #  meta=[
                                    #          ['billable', 'UBUNTU', 'total_ms'],
                                    #          ['billable', 'UBUNTU', 'jobs'],
                                    #          'run_duration_ms' 
                                    #        ])
            )
            df = self.inloop_clean( df )
            if df is None or df.empty:
                continue
            
            df['id'] = x
            data.append( df )

        if not data:
            return pd.DataFrame()
        
        dy = pd.concat( data )
        report = self.clean_all( dx, dy )

        return report

    def etl(self):
        """
        pulled from API, so raw data, for mysql
        """
        #self.runner.BigQuery.df_to_bq( report, 'Git', 'Actions', new=False )

        df = self.get_workflow_timing()
        self.runner.mysql.load_df_to_table( df , self.runner.report_name , if_exists='append' )

class PostETL:
    """
    ###################################################################
                        ## POST LOAD JOB ##
    ###################################################################
    """    
    def __init__(self):
        self.runner = GitPipelines()

    def mysql_to_bq( self ):
        df = self.runner.mysql.query_to_df( 
                f"""
                with mxdt as (
                  select max(date) as x from {self.runner.report_name} 
                )

                select 
                  t.* 
                
                from {self.runner.report_name} t 
                  cross join mxdt 
                 
                where 
                  t.fetch_date between (mxdt.x - interval 7 day ) and mxdt.x;
                """
                ) 

        if df.empty or df is None:
            raise ValueError( 'df is NoneType' )

        self.runner.BigQuery.df_to_bq( df, 'Git', 'Actions_Report', False)

    def call_modeled( self ) -> None:
        self.mysql_to_bq()

        query = self.runner.BigQuery.get_procedure('git', ['git_procedure'])
        query = query + ['call Git.aggregate(7);'] # to refresh current table if we update procedure

        for q in  query :
            try:
                job = self.runner.BigQuery.client.query(q)
                job.result()
            except Exception as e:
                print(e)

        #before select from, must trigger procedure # tapi kay atas dah buat so yeah 
        df = self.runner.BigQuery.query_to_dataframe( 'select * from Git_table.ActionsAggregate;'  ) 
        return df
    
    def send_report_to_lark(self):
        df = self.call_modeled()
        df.columns = df.columns.str.strip().str.title().str.replace('_', ' ')

        date_col = df.select_dtypes(['datetime64', 'datetime64[ns, UTC]'])

        for d in date_col:
            df[d] = df[d].apply( lambda x: int(x.timestamp() * 1000) if pd.notna(x) else None )
 
        self.runner.Lark.df_to_lark(  df, self.runner.table_id  )