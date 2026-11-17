from common.utility.genutility import *

schema = GenSchema()
class ETL:
    def __init__(self):
        self.schema = schema
    
    def generate_body( self ) -> dict:
        dt_contant = int(gen_date())
        
        return_list, purchase_list =\
        GenerateWorkingTools().generate_item()
        
        dependant_list =\
        WorkingList( self.schema, return_list, purchase_list )

        false_price, price,\
        false_quant, quant,\
        total, member_id =\
        dependant_list.get_all()

        uniqitem = [ str(c) for c in purchase_list  ]
        trid = f'{dt_contant}{''.join(uniqitem)}{member_id}'

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

    def dump_all_data(self) -> json.dump:
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

            if os.path.exists( 'dump-gen' ):
                with open( f'dump-gen/datalog{chunk}.json', 'w' ) as file:
                    json.dump( data, file, indent = 4)
                print( 'write-complete')           

            chunk += 1

            if chunk > cap:
                break

    def append_all_data(self) -> json.dump:
        data = {
                "res" : []
            }
        
        for _ in range( 1, ( 180000 )):
            x = self.generate_body()
            data['res'].append( x )
            
            print( len( data['res'] ) )

        with open( 'dump-gen/all_append.json', 'w') as f:
            json.dump( data, f, indent=4)

        return data    