import os
import pandas_gbq
import pandas as pd
from pathlib import Path

class BigQuery:
    def __init__(self, client, credits, project_id):
        self.client = client
        self.credits = credits
        self.project_id = project_id
    
    def std_cols(self, df: pd.DataFrame) -> pd.DataFrame:
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

    def query_to_dataframe( self, query ):
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