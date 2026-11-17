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


def main():
    import json
    with open("inspect.json", "r", encoding="utf-8") as f:
        res = json.load(f)

    df = pd.json_normalize( res )
    print(df)

from common.connection.larkclient import LarkClient
from common.utility.larkutillitysdk import LarkSDK
from config.lark_report_table import *
import ast

def main():
    run = LarkSDK( client=LarkClient, app_token = BASE_TOKEN, report= EMPLOYEE )
             
    # test - ignore at production
    x = run.ListTables()
    print( x )
    appendix = pd.json_normalize( x )
    print( appendix )

    name = 'PyIzzo'
    res = run.CreateBatchTable( name )

    if isinstance(  res , dict):
        pass
    else:
        ast.literal_eval( res )

    aidee = res.get('table_ids')
    aidee = aidee[0] if isinstance( aidee, list) and len( aidee ) <= 1 else aidee

    appendix.loc[ len( appendix )] = { "table_id": aidee, "name": name }
    print( appendix )

import random
import string

def main() -> pd.DataFrame : 
    """
    Before hand, I create an appendix, in order to make sure generated data can be seem :
    structured and relational **while at the same time** varies within 
    (1) date, (2) transaction_id, and any else.
    """
    all = { 
        "res" : []
    }

    smoother = 0.01
    for i in range( 1, 201 ):
        scheme = {}
        
        names = []
        for _ in range(1, random.randint( 3, 5 ) ):
            names.append(random.choice( string.ascii_letters))

        scheme_name = ''.join( names ).upper()

        scheme["id"] = i

        if i <= 30:
            scheme['category'] = "Sports"
            scheme['price'] = random.randint( 20, 100) - smoother 
        elif i > 30 and i <= 50:
            scheme['category'] = "Medical"
            scheme['price'] = random.randint( 70, 300) - smoother
        elif i > 50 and i <= 70:
            scheme['category'] = "Education"
            scheme['price'] = random.randint( 1, 30) - smoother
        elif i > 70 and i <= 120:
            scheme['category'] = "Bedrooms & Design"
            scheme['price'] = random.randint( 79, 700) - smoother
        elif i > 120 and i <= 160:
            scheme['category'] = "Kitchen & Cooks"
            scheme['price'] = random.randint( 20, 200) - smoother
        elif i > 160 and i <= 180:
            scheme['category'] = "Toilets & Laundry"
            scheme['price'] = random.randint( 10, 50) - smoother
        else:
            scheme['category'] = "Others"
            scheme['price'] = random.randint( 1, 10) - smoother

        scheme['name'] = scheme['category'].replace('&', '').replace(' ', '_').upper() + '-' + scheme_name + str( i )

        all['res'].append( scheme )

    #print( all )
    df = pd.DataFrame( all['res'] )
    print( df )
    return df

def main():
    import json
    import os
    os.makedirs('config', exist_ok=True)
          
    secrets_data = [  """${{ secrets.GITHUB }}""", """${{ secrets.LARK }}""", """${{ secrets.LARKTABLE }}""", """${{ secrets.MYSQL }}""", """${{ secrets.IZZO }}""" ]
    secrets_key = [ 'config/git.json', 'config/lark.json', 'config/lark_report_tables.json', 'config/mysql.json', 'config/izzo.json' ]
    secrets_key = [ 'git.json', 'lark.json', 'lark_report_tables.json', 'mysql.json', 'izzo.json' ] # sandbox
          
    for data, key in zip( secrets_data, secrets_key ):
        with open(key, 'w', encoding='utf-8') as f:
            f.write(data)

def main():
    from common.connection.gcpclient import GcpClient

    client = GcpClient().bq_client() 
    client.query( 'select 1;' )

if __name__ == '__main__':
    main()