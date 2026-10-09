from pipelines.gitpipelinesdk import GitSDK

def git():
    run = GitSDK()
    run.update_report_in_lark()

from common.connection.gitclient import GitClient
from common.utility.gitutility import GitRequest
import pandas as pd

def git():
    run = GitRequest( client = GitClient().declare() )
    res = run.get_runner_list() 

    print( len(res) )

    df = pd.json_normalize( res[0].get('workflow_runs') )
    print(df.info())
    print( df )

    id_list = df['id'].tolist()

    #for id in id_list:
    #    run.get_run_timing( id )
    
    res = run.get_run_timing( id_list[10] )
    import json 
    with open("response_data.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=4)
    
    return id_list


