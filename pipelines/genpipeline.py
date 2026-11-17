from common.utility.genutility import *

def generate_data_all():
    dt_contant = int(gen_date())
    schema = GenSchema()
    
    return_list, purchase_list =\
    GenerateWorkingTools().generate_item()
    
    dependant_list =\
    WorkingList( schema, return_list, purchase_list )

    false_price, price,\
    false_quant, quant,\
    total, member_id =\
    dependant_list.get_all()
    
    trid = f'{dt_contant}{str(''.join(purchase_list))}{member_id}'

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

if __name__ == '__main__':
    cap = 276 
    chunk = 0
    while chunk <= cap:
        data = {
            "res" : []
        }
        for i in range( 1, ( 649 + 1 )):
            x = generate_data_all()
            data['res'].append( x )
        print( len( data['res'] ) )

        if os.path.exists( 'dump-gen' ):
            with open( f'dump-gen/datalog{chunk}.json', 'w' ) as file:
                json.dump( data, file, indent = 4)

            print( 'write-complete')

        chunk += 1

        if chunk > cap:
            break