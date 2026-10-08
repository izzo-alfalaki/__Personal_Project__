"""
BigQuery utility is class, defined for use on detailed cases, namely uplaoding dataframe to bq,
or getting bq tables instead, or other maintainance such as procedure store / proceduire trigger

why its class instead of function, becuase we expect that BigQuery will use one client and same client, so 

instead of:

  df = fetch_data_from_api()
  client = bq_client()

  send_query( client, 'call stored_procedure();' ) 
  df = query_to_dataframe( client, 'select from recently_triggered_table;' )
   **notice how we call client twice**

we can do  :

  client = BigQuery( bq_client() )

  client.sendquery( 'query' )
  client.to_dataframe( 'query' )

minimalist within syntax
"""

import os
import pandas_gbq
import pandas as pd
from pathlib import Path

class BigQuery:
    """
    client build and connection was passed to client layers, this layers fully focused on using 
    bq_client libary. we include fexiliblity for clients but not here, since we assume multi-client
    somehow will be assigned with same task. such as reading bq table, or convert bq table to df
    or upload table to df 
    """
    def __init__(self, client, credits, project_id):
        self.client = client
        self.credits = credits
        self.project_id = project_id

    def push_query(self, query :str ) -> None:
        job = self.client.query( query )
        job.result()

        if job.errors:
            print( job.errors )
        
    def std_cols(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        make table columns standard for bq consumption
        """
        if df.empty:
            return pd.DataFrame()

        df.columns = df.columns.str.replace(r"[^a-zA-Z0-9]", "_", regex=True)
        return df

    def to_bq( self, df, destination, append= False ):
        if_exists = 'append' if append else 'replace'
    
        pandas_gbq.to_gbq( 
            dataframe=df,
            destination_table=destination,
            project_id=self.project_id,
            if_exists=if_exists,
            credentials=self.credits  
            )

    def df_to_bq( self, df , dataset, table, new= False ):
        """
        to_bq assigned for upload table, but df_to_bq, decide how to handle logic, 
        if new then append if not new then replace, and fallback, 

        if one day workflow run and api response suffer schema chaneges, so instead of fail 
        and raiseValue(), we can create a fail_appened_table. so we dont need to re-pull the response with 
        new code construct, 

        we make room for adjustment while having data alreadt arrived in database, we can use sql stimulation
        to clean data and union all, while during that, we can handle python orchestrartion to re-parse df.   
        """
        df = self.std_cols(df)
        destination = f'{dataset}.{table}'

        if not new:
            try:
                self.to_bq(df, 
                      destination, 
                      append=True)
                return print(f'appended {destination}')    
        
            except Exception as e:
                print( f'{e} for : {destination}' )
                destination = f'{destination}_failappend'
                self.to_bq( df, destination, append= True )
                return print(f'new {destination} instead')         

        if new:
            self.to_bq( df, destination, append= False )
            return print(f'replaced {destination}')

    def get_procedure( self, file_class = None, file: list = None ):
        """
        another idea, use sql instead:
        
        SELECT 
            routine_definition 
        
        FROM 
            `your_project_id.your_dataset_id.INFORMATION_SCHEMA.ROUTINES`
        
        WHERE 
            routine_name = 'your_procedure_name';
        """
        """
        get procedure from sql/ whole reading procedure, 
        we can pass it to push query, if we happen to update procedure
        """
        if not file_class:
            folder = Path('sql')
            subfolders = [f.name for f in folder.iterdir() if f.is_dir()]
            file_class = subfolders
        
        if isinstance( file_class, list):
            file_list = []
            for c in file_class:
                file_path = f'sql/{c}'
                pathlist = [f for f in os.listdir(file_path) if f.endswith('.sql') and os.path.isfile(os.path.join( file_path , f))]
                pathlist = [ ( file_path + '/' + p ) for p in pathlist  ]
                file_list.extend(pathlist)

        elif isinstance( file_class, str ):
            file_path = f'sql/{file_class}'
            pathlist = [f for f in os.listdir(file_path) if f.endswith('.sql') and os.path.isfile(os.path.join( file_path , f))]
            file_list = [ ( file_path + '/' + p ) for p in pathlist  ]

        else:
            raise ValueError( 'maynnn getcho bih ass out'  )

        if not file:
            procedure = []
            for f in file_list:
                straccess = Path( f ).read_text( encoding = 'utf-8' )
                procedure.append( straccess )
            return procedure

        if file:
            file = [ x + '.sql' for x in file if not '.sql' in x  ]
            file_name = [ f for f in file_list if any(f.endswith(x) for x in file) ]

            procedure = []
            for f in file_name:
                straccess = Path( f ).read_text( encoding = 'utf-8' )
                procedure.append( straccess )
            return procedure

    def query_to_dataframe( self, query : str|list[str] ):
        """
        this function is to convert a query result(s) to dataframe, if  query were pished as list, 
        then we can collect all the results without concating them, meanwhlle, for one sql string, 
        will just return the pd.Dataframe
        """
        if isinstance( query, list ):
            alldata = {}
            for q, i in zip( query, range(1, len(query), 1 ) ):
                try:
                    df = self.client.query( q ).to_dataframe()
                except Exception as e:
                    print(e)
                    print( f'{q} error, using empty dataframe' )
                    df = pd.DataFrame()
            
                name = f'query_{i}'
                alldata[name] = df

            return alldata

        if isinstance( query, str ):
            try:
                df = self.client.query( query ).to_dataframe()
            except Exception as e:
                print(f'query error: {e}')
                return pd.DataFrame()
        
            return df