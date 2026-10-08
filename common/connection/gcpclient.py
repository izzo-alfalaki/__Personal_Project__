"""
this is gcp client for izzo, a personal service-account running around google workspace,
was created on IAM at console. This py file simply build our gcp client by passing
Athorization, Authentaction, scopes, roles and credientals. 

by making this layers, we can now:
   centralize any client issues issued or error on connection during workflow execution
   - centralizing connectivity simply equal to : making a source-of-truth that controls everything
"""

import gspread
from google.cloud import bigquery
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from config.config import *

role = ['https://www.googleapis.com/auth/spreadsheets'
        , 'https://www.googleapis.com/auth/drive'
        , 'https://www.googleapis.com/auth/bigquery']

class GcpClient:
    """
    calling this client simply just import, and for configuration, 
    we dont need to handle them further, which mean :
      # WE ASSUME ONE SERVICE ACCOUNT WILL RUN ENTIRE WORKFLOW #
    either way, if we had more than one gcp client, we can stimulate code here, 
     : by include requrement for self.json_key_path at orchestration layer. 
    """
    def __init__(self):
        self.role = role
        
        jsonpath = 'izzo.json'
        self.json_key = get_path( jsonpath )
        
        jsonload = get_json( jsonpath )
        self.project_id = jsonload.get( 'project_id', None )
        
    def get_credits( self ):
        return Credentials.from_service_account_file(self.json_key, scopes=role)

    def bq_client( self ):        
        credits = self.get_credits()
        return bigquery.Client(credentials=credits, project=self.project_id)

    def drive_client(self):
        credits = self.get_credits()
        return build("drive", "v3", credentials=credits)

    def sheet_client( self ):
        credits = self.get_credits()
        return gspread.authorize(credits)