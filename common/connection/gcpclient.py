import gspread
from google.cloud import bigquery
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from config.config import *

role = ['https://www.googleapis.com/auth/spreadsheets'
        , 'https://www.googleapis.com/auth/drive'
        , 'https://www.googleapis.com/auth/bigquery']

class GcpClient:
    def __init__(self):
        self.role = role
        
        jsonpath = 'izzo.json'
        self.json_key = get_path( jsonpath )
        
        jsonload = get_json( jsonpath )
        self.project_id = jsonload.get( 'project_id', 'izzo-472202' )
        
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