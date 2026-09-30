import json
import pandas as pd
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *

class LarkSDK:
    def __init__(self, client : classmethod , app_token, report : dict ):
        self.token = client.lark_access_token()
        self.client = client.SDKclient()

        self.table_id = report.get( 'TABLE_ID' )
        self.record_id = report.get( 'RECORD_ID' )

        self.base_token = app_token

    def df_to_records(self, df: pd.DataFrame):
        date_col = [ c for c in df.select_dtypes( include=[ 'datetime', 'datetime64', 'datetime64[ms, UTC]' ]).columns ]
        
        for c in date_col:
            df[c] = (df[c].astype("int64") // 10**6)

        load = df.to_dict(orient="records")
                
        return load

    def load_record( self, load ):
        load_records = [
                    AppTableRecord.builder().fields(record).build()
                    for record in load
                ]
        return load_records

    def log_return( self, response ):
        if not response.success():
            lark.logger.error(
                f"client.failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}, message: {response.error.get('message') if response.error else None}" 
                #- resp: \n{json.dumps(json_res, indent=4, ensure_ascii=False)}
            )
            return None
        
        json_str = lark.JSON.marshal(response.data)
        data = json.loads( json_str )
        return data
                    
    def ListTables(self):
        request: ListAppTableRequest = ListAppTableRequest.builder() \
            .app_token(self.base_token) \
            .page_token(self.table_id) \
            .page_size(10) \
            .build()

        response: ListAppTableResponse = self.client.bitable.v1.app_table.list(request)
        x = self.log_return( response)

        if x is None:
            raise ValueError( 'None Type Response' )

        return x
    
    def CreateBatchTable( self, name ):
        request: BatchCreateAppTableRequest = BatchCreateAppTableRequest.builder() \
            .app_token(self.base_token) \
            .request_body(BatchCreateAppTableRequestBody.builder()
                .tables([ReqTable.builder()
                .name(name)
                .build()
                ])
                .build()) \
            .build()

        response: BatchCreateAppTableResponse = self.client.bitable.v1.app_table.batch_create(request)
        x = self.log_return(response)
        
        return x

    def CreateRecords( self, df ):
        """
        schema:
        {
            "GroupChat":[{"id":"oc_cd07f55f14d6f4a4f1b51504e7e97f48"}],
            "attachment":[{"file_token":"DRiFbwaKsoZaLax4WKZbEGCccoe"},{"file_token":"BZk3bL1Enoy4pzxaPL9bNeKqcLe"},{"file_token":"EmL4bhjFFovrt9xZgaSbjJk9c1b"},{"file_token":"Vl3FbVkvnowlgpxpqsAbBrtFcrd"}],
            "barcode":"qawqe",
            "checkbox":true,
            "currency":3,
            "date":1674206443000,
            "duplex_link":["recHTLvO7x","recbS8zb2m"],
            "location":"116.397755,39.903179",
            "multi_select":["option_1","option_2"],
            "number":100,
            "phone":"13026162666",
            "progress":0.25,
            "rating":3,
            "single_link":["recHTLvO7x","recbS8zb2m"],
            "single_select":"option_1",
            "text":"text",
            "url":{"link":"https://www.larksuite.com/product/base","text":"Base"},
            "user":[{"id":"ou_2910013f1e6456f16a0ce75ede950a0a"},{"id":"ou_e04138c9633dd0d2ea166d79f548ab5d"}]
        }
        """
        load = self.df_to_records( df )

        request: BatchCreateAppTableRecordRequest = BatchCreateAppTableRecordRequest.builder() \
            .app_token(self.base_token) \
            .table_id(self.table_id) \
            .request_body(BatchCreateAppTableRecordRequestBody.builder()
                .records(self.load_record(load))
                .build()) \
            .build()

        response: BatchCreateAppTableRecordResponse = self.client.bitable.v1.app_table_record.batch_create(request)
        x = self.log_return( response )

        return x

    def UpdateRecordData( self, df ):
        """
        Actually ignore this guy ah, update is not really needed for now but maybe some occasion we do ah
        """
        """
        request: UpdateAppTableRecordRequest = UpdateAppTableRecordRequest.builder() \
                .app_token("appbcbWCzen6D8dezhoCH2RpMAh") \
                .table_id("tblsRc9GRRXKqhvW") \
                .record_id("recPGfZZ13") \
                .user_id_type("open_id") \
                .ignore_consistency_check(True) \
                .request_body(AppTableRecord.builder()
                    .fields({
                                "attachment":[{"file_token":"DRiFbwaKsoZaLax4WKZbEGCccoe"},{"file_token":"BZk3bL1Enoy4pzxaPL9bNeKqcLe"},{"file_token":"EmL4bhjFFovrt9xZgaSbjJk9c1b"},{"file_token":"Vl3FbVkvnowlgpxpqsAbBrtFcrd"}],
                                "barcode":"qawqe",
                                "checkbox":true,
                                "currency":3,
                                "date":1674206443000,
                                "duplex_link":["recHTLvO7x","recbS8zb2m"],
                                "groupChat":[{"id":"oc_cd07f55f14d6f4a4f1b51504e7e97f48"}],
                                "location":"116.397755,39.903179",
                                "multi_select":["option_1","option_2"],
                                "number":100,
                                "phone":"130xxxx2666",
                                "progress":0.25,
                                "rating":3,
                                "single_link":["recHTLvO7x","recbS8zb2m"],
                                "single_select":"option_1",
                                "text":"text",
                                "url":{"link":"https://www.larksuite.com/product/base",
                                "text":"Base"},
                                "user":[{"id":"ou_2910013f1e6456f16a0ce75ede950a0a"},{"id":"ou_e04138c9633dd0d2ea166d79f548ab5d"}]
                            }
                             ).build()) \
                .build()
        """
        laod = self.df_to_records( df )

        request: UpdateAppTableRecordRequest = UpdateAppTableRecordRequest.builder() \
            .app_token(self.base_token) \
            .table_id(self.table_id) \
            .record_id( self.record_id ) \
            .request_body(AppTableRecord.builder()
                .fields( self.load_record(laod) )
                .build()) \
            .build()

        response: UpdateAppTableRecordResponse = self.client.bitable.v1.app_table_record.update(request)
        x = self.log_return( response )
        
        return x