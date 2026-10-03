from common.utility.larkutillitysdk import LarkSDK
from common.connection.larkclient import LarkClient
from config.lark_report_table import IZZO_TABLE, BASE_TOKEN as APP_TOKEN

req = LarkSDK( LarkClient(), APP_TOKEN, IZZO_TABLE )

import pandas as pd
df = pd.DataFrame( { 'name' : [ 'izzat', 'rosnazifa', 'ISHAK' ], 'number' : [ 276, 37, 276 ] } )

res = req.SearchRecord()

print( res )

df = pd.json_normalize( res )

#df.to_csv( 'izzat.csv', index=False )

for c in df.columns:
    df[c] = df[c].apply( lambda x: x[0]['text'] if (isinstance( x, list ) and x[0]['text']) else x )

df.columns = df.columns.str.replace( 'fields.', '' ).str.replace('.',  '_')

print( df )

#    def log_return( self, response ):
#        if not response.success():
#            lark.logger.error(
#                f"client.failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, message: {response.error.get('message') if response.error else None}" 
#                #- resp: \n{json.dumps(json_res, indent=4, ensure_ascii=False)}
#            )
#            return None
#        
#        json_str = lark.JSON.marshal(response.data)
#        print( json_str )
#        data = json.loads( json_str )
#        print( data )
#        return data