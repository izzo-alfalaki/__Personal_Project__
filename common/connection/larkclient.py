"""
there is two client in lark, simply asses

LarkClient.SDKclient for using alrk_oapi, meanhwile, 
for classsic requests method, call LarkClient.declare, this, will return a dict, 

**access token for: header, so token not really that needed in return, but 
                    just in case .**

"""

import requests
import lark_oapi as lark
from config.larkconfig import APP_ID, APP_SECRET

class LarkClient:
    def __init__(self):
        """
        self.base_token = is not passed / handle here, because : 
        one app can walk around lark bases freely as long as organization include the app name in their workspace,
        therefor, using one app, we can work on many bases,
        anddd instead of updating self.base_token everytime, simply just passed each to udf
        """
        self.APP_ID = APP_ID
        self.APP_SECRET = APP_SECRET
        
    def lark_access_token( self ):
        url = 'https://open.larksuite.com/open-apis/auth/v3/tenant_access_token/internal'
        payload = {
            'app_id': self.APP_ID,
            'app_secret': self.APP_SECRET
            }
        
        res = requests.post(url, json=payload)
        data = res.json()
        if data.get('code') != 0:
            raise ValueError('Failed to get access token')
        
        return data.get('tenant_access_token' , None)

    def header(self):
        token = self.lark_access_token()

        if token is None:
            raise ValueError( 'access token is nonetype' )

        headers = { 'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json' }

        return headers

    def declare( self ):
        """
        instead of having users to build each by 
        LarkClient.lark_access_token() and LarkClient.header(), we simply call
        LarkClient.declare(), now we had all needed config within a dictinory, and 
        simply un-package them when we need to use it.
        """
        return dict( zip( [ 'token', 'header' ], [ self.lark_access_token(), self.header() ] ) )

    def SDKclient( self ):
        """
        Lark provide sdk, therefore, we showcase two way method of using Lark, which was
        per hardcode header + body, and import from libary
        """
        return lark.Client.builder().app_id(self.APP_ID).app_secret(self.APP_SECRET).log_level(lark.LogLevel.DEBUG).build()

