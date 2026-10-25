from pipelines.larkpipelines import LarkPipelines
import pandas as pd

def clean_employee_table(df : pd.DataFrame ) -> pd.DataFrame:
    
    num_cols_need_clean = [  
            'contract left ( month )_value', 'loyalty payout_value', 'resign notice ( days )_value'
        ]

    for c in num_cols_need_clean:
        df[c] = df[c].astype( str )
        df[c] = pd.to_numeric( df[c], errors = 'coerce')
        df[c] = df[c].fillna(0)

    return df

def clean_salary_table():
    ...

if __name__ == '__main__':
    run = LarkPipelines()
    df = run.lark_get_table_list()
    
    """
    reading one table on;y
    """
    # mask = df['name'].str.lower().str.contains('employee')
    # employee = df.loc[mask , 'table_id'].iloc[0]
    
    # df = run.get_report_from_lark( new_table_id = employee) 
    # df.to_csv( 'pre_clean.csv')
    """
    handling all table within response list
    """
    all_tables = {}
    for key, table_id in zip( df['name'].unique().tolist(), df['table_id'].unique().tolist() ):
        df = run.get_report_from_lark( new_table_id = table_id )

        df = clean_employee_table(  run.general_standard_clean(df) )
        df.to_csv( f'{key}_post_clean.csv')

        all_tables[ key ] = df
    
        try:
            run.send_report_to_mysql( df )
        except Exception as e:
            print(e)
            pass