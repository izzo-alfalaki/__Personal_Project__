""" 
This pipeliens utilize the request methid of Lark, in other .py, we will demonstrate Lark SDK
"""
import ast
import numpy as np
import pandas as pd

from common.connection.gcpclient import GcpClient
from common.utility.bigqueryutility import BigQuery

from common.connection.gitclient import GitClient
from common.utility.gitutility import GitRequest
from common.connection.mysql import MysqlClient
from common.utility.mysqlutility import MySQL

from common.utility.larkutility import LarkRequests
from common.connection.larkclient import LarkClient
from common.utility.larkutillitysdk import LarkSDK

from config.lark_report_table import BASE_TOKEN as APP_TOKEN, GIT_REPORT

class Runner:
    def __init__(self, local : bool = False ):
        self.Git = GitRequest(GitClient().declare())
        self.Lark = LarkRequests( LarkClient().declare(), APP_TOKEN)
    
        gcp = GcpClient()
        self.BigQuery = BigQuery( gcp.bq_client(), gcp.get_credits(), gcp.project_id )
        
        if not local:
            client= MysqlClient().engine(  user_package = 'izzo', database = 'raw' )
        if local:
            client = MysqlClient().retry_engine(  user_package = 'izzo', database = 'raw' )
        self.mysql = MySQL( client ) 
        
        self.table_id = GIT_REPORT.get('TABLE_ID')
        self.report_name = 'git_actions'

class ETL:
    """
    ###################################################################
                            ## ETL ##
    ###################################################################
    """    
    def __init__(self, runner) :
        self.runner = runner or Runner()

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

        df = df.drop( columns = 'billable.UBUNTU.job_runs')

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
        report = report.rename( columns = { 'billable.UBUNTU.jobs' : 'assigned_job_count'} )

        #report.to_parquet( 'actionrun_apipull.parquet' )        
        return report

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
            
            try:
                df = self.inloop_clean( df )
            except Exception as e:
                print( f'in loop clean fail : {e}')
                pass     
            
            if df is None or df.empty:
                continue
            
            df['id'] = x
            data.append( df )

        if not data:
            return pd.DataFrame()
        
        dy = pd.concat( data )

        try:
            report = self.clean_all( dx, dy )
        except Exception as e:
            print( f'cleaaning-all data has error : {e}')
            report = dy
            # since we pass an error un-standard dy, we will need to create a fail handler in load_to_mysql
            # when append fail = create new table with fail and timestamp of fail so we can later refer in mysql whats schema has drift / change 

        return report

    def load_to_mysql(self, df : pd.DataFrame ):
        """
        pulled from API, so raw data, for mysql
        """
        #self.runner.BigQuery.df_to_bq( report, 'Git', 'Actions', new=False )

        results = []
        if df is None or df.empty:
            print( 'null df, empty df at stage Upload to MySQL' )
            results.append( 'null_df' )
        
        try:
            self.runner.mysql.load_df_to_table( df , self.runner.report_name , if_exists='append' )
            results.append( f'completed successfully : {self.runner.report_name}' ) 
        except:
            try:
                for c in df.columns:
                    df[c] = df[c].astype( str )

                new_name = f"{ self.runner.report_name }_failed_{pd.Timestamp.now().strftime('%Y%m%d%_H%M%S')}"
                self.runner.mysql.load_df_to_table( df , new_name , if_exists='replace' )
                results.append( f'completed : {new_name}' )
            except Exception as e:
                results.append( f'{new_name} : {e}' )
                print( f'new_table also fail : {e}')

        return results    

            # this allow us to trouble shoot faster, in meantime, to make sure storage does not fed too much, quickly troubleshoot
            # meanwhile, we can also ignore airflow retry concept, rather - go to db and clean table and union to `self.runner.report_name` and re-run checkpoint only

    # IN AIRFLOW, WE WRAP ETL TO THIS, USE TWO ABOVE AS TASK AND CONVERT THIS AS DAGS
    def etl(self):
        """
        pulled from API, so raw data, for mysql
        """
        #self.runner.BigQuery.df_to_bq( report, 'Git', 'Actions', new=False )

        df = self.get_workflow_timing()
        results = self.load_to_mysql( df = df )

        return df

class PostETL:
    """
    ###################################################################
                        ## POST LOAD JOB ##
    ###################################################################
    """    
    def __init__(self, runner) :
        self.runner = runner or Runner()

    def from_mysql( self ) -> pd.DataFrame:
        df = self.runner.mysql.query_to_df( 
                f"""
                with mxdt as (
                    select max(cast( left( unique_timestamp, 19 ) as datetime )) as x from git_actions  
                    )
                select 
                    t.*             
                from 
                    git_actions t cross join mxdt 
                where 
                    cast( left( t.unique_timestamp, 19 ) as datetime ) between (mxdt.x - interval 7 day ) and mxdt.x;
                """
                ) 

        if df.empty or df is None:
            return pd.DataFrame()

        return df

    def to_bigquery( self, df: pd.DataFrame ):
        if df is None or df.empty:
            raise KeyError( 'to_bigquery stage cacth empty dataframe, there is error at gitpipelines.py/PostETL().from_mysql() ')

        try:    
            self.runner.BigQuery.df_to_bq( df, 'Git', 'GitActions', True)
            return f'upload successfull'    
        except Exception as e: 
            return f'error to send to BigQuery : {e}'
            
    def push_procedure( self ) -> None:
        query = [ 'call Git.aggregate();', 'call Git.model(7);' ]
        
        results = {}
        for q in query:
            try:
                job = self.runner.BigQuery.client.query(q)
                job.result()
                results[q] = f"success:{job.job_id}" 
            except Exception as e:
                print(e)
                results[q] =  str(e) 

        return results

#########################################################################################################################
# -------------------------------------------- BREAK OF SIGNIFICANT METHOD -------------------------------------------- #
#########################################################################################################################
class CallProcedureSendToLark:
    def __init__(self):
        self.runner = GitPipelines()

    def push_procedure( self ) -> None:
        query = self.runner.BigQuery.get_procedure('git', ['git_procedure'])
        query = query + ['call Git.aggregate(7);'] # to refresh current table if we update procedure

        for q in  query :
            try:
                job = self.runner.BigQuery.client.query(q)
                job.result()
            except Exception as e:
                print(e)
        
    def get_modeled_table( self ) -> pd.DataFrame:
        df = self.runner.BigQuery.query_to_dataframe( 'select * from Git_table.ActionsAggregate;'  ) 
        return df

    def clean_table_for_lark( self, df : pd.DataFrame ) -> pd.DataFrame:
        df.columns = df.columns.str.strip().str.title().str.replace('_', ' ')

        date_col = df.select_dtypes(['datetime64', 'datetime64[ns, UTC]'])

        for d in date_col:
            df[d] = df[d].apply( lambda x: int(x.timestamp() * 1000) if pd.notna(x) else None )
    
    def send_report_to_lark(self, df):  
        self.runner.Lark.df_to_lark(  df, self.runner.table_id  )

    # SIMILARLY, WE WILL WRAP ALL IN POST_ETL TO MAKE DAGS, AND DAGS WILL LOOK LIKE THIS ( INTERNALLY NOT SYNTAX-LY)  
    def post_etl( self ):
        # declare post_ETL : run = PostETL()

        # assume we dont use self
        df = self.from_mysql()
        self.to_bigquery(df )
        self.push_procedure()
        finaldf = self.get_modeled_table()

        return finaldf
class CallProcedureSendToLark_UsingSDK:
    def __init__(self):
        self.Git = GitRequest(GitClient().declare())
        self.Lark = LarkSDK( LarkClient(), APP_TOKEN, GIT_REPORT)

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

    def main( self ):
        self.recall_workflow()
        self.send_report_to_lark()