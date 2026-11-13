from pipelines.larkpipelines import LarkPipelines
import pandas as pd
import ast

def clean_employee_table(df : pd.DataFrame ) -> pd.DataFrame:
    
    num_cols_need_clean = [  
            'age_value' , 'available leave this year_value' , 'contract left ( month )_value' , 'loyalty payout_value' , 'requestabe annual leave_value' , 'resign notice ( days )_value' , 'cummulative performance_value'
        ]

    for c in num_cols_need_clean:
        df[c] = df[c].apply(lambda x: x[0] if x[0] and len(x) > 0 else '0')
        df[c] = pd.to_numeric( df[c], errors = 'coerce')
        df[c] = df[c].fillna(0)

    df.columns = df.columns.str.split( '_' ).str[0]
    return df

def clean_salary_table(df : pd.DataFrame, production : bool = False ) -> pd.DataFrame:
    for x in [ 'qualified position', 'base bonus_value', 'base pay_value']:  
        df[x] = df[x].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        if not x == 'qualified position':
            df[x] = df[x].apply(lambda x: x[0] if len(x) <= 1 else x)

    if production:
        if 'qualified position' in df.columns:
            df = df.explode('qualified position')
        else:
            print('WARNING: qualified position column not found in dataframe')
    
    return df

def main( production : bool = False ):
    run = LarkPipelines()
    df = run.lark_get_table_list()
    if df.empty:
        raise ValueError('No tables found in LarkBase.')

    if not production:
        df.to_csv( 'list_of_tables.csv', index=False )

    manual_key = [ 'Employee Table', 'Salary Table' ]
    test_table_id = [ df['table_id'].tolist()[0], df['table_id'].tolist()[1]]
   
    zip_package = zip( df['name'].unique().tolist(), df['table_id'].unique().tolist() )
    
    tables = {}
    for key, id in zip_package if production else zip( manual_key, test_table_id ):
        fetch_df = run.get_df_from_table_id( new_table_id = id )

        if fetch_df.empty:
            df = pd.DataFrame()
            pass

        if not production:
            fetch_df.to_csv( f"raw_{key.lower().replace(' ', '_')}_table.csv", index=False )

        if key == 'Employee Table':
            fetch_df = clean_employee_table( fetch_df )
        elif key == 'Salary Table':
            fetch_df = clean_salary_table( fetch_df )
        else:
            print( f'{key}: not assigned post clean' )
        
        tables[key] = fetch_df

        if production:
            try:
                run.send_report_to_mysql( df )
            except Exception as e:
                print(e)
                pass
        else:
            fetch_df.to_csv( f"mysql_{key.lower().replace(' ', '_')}_table.csv", index=False )

if __name__ == '__main__':
    main(production=True)
    