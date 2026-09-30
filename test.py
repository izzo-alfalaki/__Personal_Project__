from common.utility.larkutillitysdk import LarkSDK
from common.connection.larkclient import LarkClient
from config.lark_report_table import IZZO_TABLE, BASE_TOKEN as APP_TOKEN

req = LarkSDK( LarkClient(), APP_TOKEN, IZZO_TABLE )

import pandas as pd
df = pd.DataFrame( { 'name' : [ 'izzat', 'rosnazifa', 'ISHAK' ], 'number' : [ 276, 37, 276 ] } )

name = 'Izzo Table'
res = req.UpdateRecordData( df )