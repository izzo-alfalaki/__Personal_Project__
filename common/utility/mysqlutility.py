import json
import pandas as pd
from sqlalchemy import text

class MySQL:
    def __init__(self, client):
        self.engine = client

    def query_to_df(self, query: str, params: dict | None = None) -> pd.DataFrame:
        with self.engine.connect() as connection:
            return pd.read_sql(sql=text(query), con=connection, params=params)

    def execute_statement(self, sql_statement: str, params: dict | None = None) -> int:
        with self.engine.begin() as connection: 
            result = connection.execute(text(sql_statement), params or {})
            return result.rowcount

    def clean_table(self, df : pd.DataFrame):
        """
        most database ive dealt are usually need of a good columns name, 
        and cant have any list or dict as object, so heres my stdzation
        """
        df.columns = df.columns.str.strip().str.lower().str.replace(r"[^\w]+", "_", regex=True)

        date_col = [ c for c in df.columns if 'date' in c ]
        for c in date_col:
            df[c] = pd.to_datetime( df[c], errors='coerce', format = 'mixed' )

        for col in df.columns:
            if ( df[col].apply(lambda x: isinstance(x, (list, dict))).any()):
                df[col] = df[col].apply( lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x )
            
        return df

    def load_df_to_table( self, df: pd.DataFrame, table_name: str, if_exists: str = "append" ) -> None:
        df = self.clean_table(df)

        with self.engine.begin() as connection:
            df.to_sql(
                name=table_name,
                con=connection,
                if_exists=if_exists,
                index=False,
                chunksize=1000
            )