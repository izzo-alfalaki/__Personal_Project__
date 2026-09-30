import requests
import lark_oapi as lark
from config.larkconfig import APP_ID, APP_SECRET

class LarkClient:
    def __init__(self):
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
        return dict( zip( [ 'token', 'header' ], [ self.lark_access_token(), self.header() ] ) )

    def SDKclient( self ):
        return lark.Client.builder().app_id(self.APP_ID).app_secret(self.APP_SECRET).log_level(lark.LogLevel.DEBUG).build()
