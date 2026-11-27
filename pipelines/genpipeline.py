from common.connection.gcpclient import GcpClient
from common.utility.bigqueryutility import BigQuery

from common.connection.mysql import MysqlClient
from common.utility.mysqlutility import MySQL
from common.utility.genutility import *

class Runner:
    def __init__(self, local : bool = False ):
        self.schema = GenSchema()
        
        if not local:
            client= MysqlClient().engine(  user_package = 'izzo', database = 'raw' )
        if local:
            client = MysqlClient().retry_engine(  user_package = 'izzo', database = 'raw' )
        self.mysql = MySQL( client ) 

        self.bigquery = BigQuery( client = GcpClient().bq_client(), 
                                  credits = GcpClient().get_credits(),
                                  project_id= GcpClient().project_id )

class GenerateBody:
    def __init__(self, runner ):
        self.runner = runner or Runner()
    
    def generate_body( self ) -> dict:
        dt_contant = int(gen_date())
        
        return_list, purchase_list =\
        GenerateWorkingTools().generate_item()
        
        dependant_list =\
        WorkingList( self.runner.schema, return_list, purchase_list )

        false_price, price,\
        false_quant, quant,\
        total, member_id =\
        dependant_list.get_all()

        uniqitem = [ str(c) for c in purchase_list  ]
        trid = f"{dt_contant}{''.join(uniqitem)}{member_id}"

        return\
{
 "transaction_id" : trid,
 "response" : { 
               "date" : dt_contant,
               "basket" : {
                   "confirmed_item" : { "items" : purchase_list,
                                        "quantity" : quant,
                                        "price" : price }, 
                   "returned_item" : { "items" : return_list,
                                       "quantity" : false_quant,
                                       "price": false_price }
               },
               "total" : total,
               "membership_id" : member_id 
               }
}

    def dump_all_data(self, local : bool = False ) -> json.dump:
        cap = 276 
        chunk = 0
        while chunk <= cap:
            data = {
                "res" : []
            }
            for _ in range( 1, ( 649 + 1 )):
                x = self.generate_body()
                data['res'].append( x )
            print( len( data['res'] ) )

            if local:
                if os.path.exists( 'dump-gen' ):
                    with open( f'dump-gen/datalog{chunk}.json', 'w' ) as file:
                        json.dump( data, file, indent = 4)
                    print( 'write-complete')

            if not local:
                return data           

            chunk += 1

            if chunk > cap:
                break

    def dump_all_data( self ) -> dict:
        data = {
            'res' : []
        }

        for _ in range( 1, ( 276 + 649) ):
            data["res"].append( self.generate_body() ) 

        return data

class ETL:
    def __init__(self, runner):
        self.runner = runner or Runner()

    def get_response( self, response : dict ) -> pd.DataFrame :
        if response is None or not response:
            print( 'response error : Expected dict but got Nonetype / or null dict ')
            return pd.DataFrame()
        
        if response.get( 'res' ):
            try:
                data = response.get( 'res' )
                return pd.json_normalize( data )

            except Exception as e:
                print( e )
                return pd.DataFrame()

    def clean_response( self, df : pd.DataFrame ) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()

        df = df.rename( columns= {                                 
            "response.date" : "date",                             
            "response.basket.confirmed_item.items" :  "confirmed_item",     
            "response.basket.confirmed_item.quantity" : "confirmed_item_quantity",  
            "response.basket.confirmed_item.price" : "confirmed_item_price",     
            "response.basket.returned_item.items" : "returned_item",       
            "response.basket.returned_item.quantity" : "returned_item_quantity",   
            "response.basket.returned_item.price" : "returned_item_price",      
            "response.total" : "total",                           
            "response.membership_id" : "membership_id"                      
        }) 
        df = df.drop_duplicates( subset='transaction_id', ignore_index=False )

        df['date'] = pd.to_datetime( df['date'], unit='s')
        for c in [ 'transaction_id', 'membership_id' ]:
            df[c] = df[c].astype( str )
        
        return df  
    
    def load_to_mysql( self, df : pd.DataFrame ) -> None :
        if df.empty or df is None:
            print( 'passed df for load_mysql is null, passing this stage instead' )
            return 

        try:
            self.runner.mysql.load_df_to_table( df, 'transaction_data', if_exists='append')
        except Exception as e:
            print( f'mysql expereince error : {e}')
            try:
                new_name = f"transaction_data_fail_{pd.Timestamp.now().strftime( '%Y%m%d_%H%M%S' )}"
                self.runner.mysql.load_df_to_table( df, new_name, if_exists='replace')
            except Exception as er:
                print( f'failure on new destinantion tables as well : {er} '  )
                pass

class PostETL:
    """
    ###################################################################
                        ## POST LOAD JOB ##
    ###################################################################
    """    
    def __init__(self, runner):
            self.runner = runner or Runner()

    def from_mysql( self ) -> pd.DataFrame:
        df = self.runner.mysql.query_to_df( 
                f"""
                with a as (
                select 
                    *, ROW_NUMBER() over ( 
                        PARTITION BY transaction_id ORDER BY `date` desc 
                    ) as rn   
                from transaction_data 
                ) 
                (
                select * from a WHERE rn = 1 and 
                (
                    unique_timestamp BETWEEN 
                        DATE_SUB( date( CURRENT_TIMESTAMP()), INTERVAL 7 DAY ) 
                        and 
                        date( CURRENT_TIMESTAMP() )
                )
                order by total desc  limit 2763
                )                
                union ALL
                (
                select * from a WHERE rn = 1 and 
                (
                    unique_timestamp BETWEEN 
                        DATE_SUB( date( CURRENT_TIMESTAMP()), INTERVAL 7 DAY ) 
                        and 
                        date( CURRENT_TIMESTAMP() )
                )
                order by total asc  limit 649
                );
                """
                ) 

        if df.empty or df is None:
            try: 
                df = df = self.runner.mysql.query_to_df( "select * from transaction_data;" )
            except Exception as e:
                print( e )
                return pd.DataFrame()

        return df

    def to_bigquery( self, df: pd.DataFrame ):
        if df is None or df.empty:
            raise KeyError( 'to_bigquery stage cacth empty dataframe, there is error at genpipelines.py/PostETL().from_mysql() ')
            #return None

        list_cols = [ 'confirmed_item', 'confirmed_item_quantity', 'confirmed_item_price', 
                      'returned_item', 'returned_item_quantity', 'returned_item_price' ]
        
        try:    
            self.runner.bigquery.df_to_bq( df, 'GenData', 'TransactionData', True, list_exists = list_cols)
            return f'upload successfull'    
        except Exception as e: 
            return f'error to send to BigQuery : {e}'

    def push_appendix( self ) -> None:
        df = self.runner.mysql.query_to_df( 'select DISTINCT id, category, price, name from gen_appendix;' ) 
        
        if df.empty or df is None:
            return f'Appendix-Job: null pd.DataFrame()'

        try:    
            self.runner.bigquery.df_to_bq( df, 'GenData', 'Appendix', True)
            return f'Appendix-Job: upload successfull'    
        except Exception as e: 
            return f'Appendix-Job: {e}'        

    def push_procedure( self ) -> None:
        query = 'call GenData.model()'
        results = {}

        try:
            job = self.runner.bigquery.client.query(query)
            job.result()
            results[query] = f"success:{job.job_id}" 
        except Exception as e:
            print(e)
            results[query] =  str(e) 

        return results
class NotUsed:
    def __init__(self, body_generator : classmethod ):
        if callable( body_generator):
            self.body = body_generator

    def append_all_data(self) -> json.dump:
        """
        not for use now
        """
        data = {
                "res" : []
            }
        
        for _ in range( 1, ( 180000 )):
            x = self.body()
            data['res'].append( x )
            
            print( len( data['res'] ) )

        with open( 'dump-gen/all_append.json', 'w') as f:
            json.dump( data, f, indent=4)

        return data    