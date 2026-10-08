"""
This is integration layer:
Integrating between Lark to platform of choices.
LarkRrequests expect client from LarkClient, unlike Git, Lark bot was created on 
personal account, then any organization that want the automation implement, can 
simply add / share their base to the app, upon connected or granted access, we can then 
start working on any base. 

LarkRequest feeds on it client, where we stimulate the client at orchestration layer, and
base token as well. for example:

====================================
run = LarkRequest( LarkClient(), base_token = base_A)

* stimulate base A *
* then we want to change base *

run.base_token = base_B

* continue stimulation *
====================================
this class use http method, in other class, we will demonstrate official lark sdk
main reference:
  https://open.larksuite.com/document/server-docs/docs/bitable-v1/bitable-overview
"""
import math
import time
import requests

class LarkRequests:
    def __init__(self, client : dict, base_token):
        larkclient = client
        self.access_token = larkclient.get( 'token' )
        self.header = larkclient.get('header')
        self.base_token = base_token
    
    def lark_get_table( self, table_id):
        """
        this func use to read-table, 
        essential for constructing from all the way read table to push table to database
        """
        path = f'https://open.larksuite.com/open-apis/bitable/v1/apps/{self.base_token}/tables/{table_id}/records'

        all_items = []
        page_token = None
        
        while True:
            params = {'page_size': 500}
            if page_token:
                params['page_token'] = page_token
                
                res = requests.get(path, headers=self.header, params=params)
                data = res.json()

            if data.get('code') != 0:
                raise Exception(f"Fetch error: {data}")

            items = data['data']['items']
            all_items.extend(items)

            if not data['data'].get('has_more'):
                break

            page_token = data['data'].get('page_token')
        
        return all_items

    def clear_table( self, table_id):
        """
        if we are assigned to update a report in Lark, we may need this,
          clear old table then paste new table
        """
        path = f'https://open.larksuite.com/open-apis/bitable/v1/apps/{self.base_token}/tables/{table_id}'

        all_record_ids = []
        page_token = None

        while True:
            url = f'{path}/records?page_size=100'
            
            if page_token:
                url += f'&page_token={page_token}'

            res = requests.get(url, headers=self.header)
            data = res.json()

            if data.get('code') != 0:
                raise Exception(f'Fetch records error: {data}')
            
            items = data['data']['items']
            
            for item in items:
                all_record_ids.append(item['record_id'])
                
            page_token = data['data'].get('page_token')

            if not page_token:
                break

        print(f'Total records to delete: {len(all_record_ids)}')

        batch_size = 100
        total = len(all_record_ids)

        for i in range(0, total, batch_size):
            batch_ids = all_record_ids[i:i + batch_size]

            delete_url = f'{path}/records/batch_delete'

            payload = {
                'records': batch_ids
                }

            res = requests.post(delete_url, headers=self.header, json=payload)
            data = res.json()

            if data.get('code') != 0:
                raise Exception(f'Delete error: {data}')
            
            print(f'Deleted {i + len(batch_ids)}/{total}')

            time.sleep(0.2)

        print('Table cleared successfully')
 
    def df_to_lark(self, df, table_id, batch_size=100, max_retries=3):
        """
        in orchestration layers, we can use like this
        df = client.query().to_dataframe()
        
        delete_lark_table( table_need_to_update_id )

        # then send the updated model
        df_to_lark( df, table_need_to_update_id )
        # almost like updating a data underlying dashboard
        """
        url = f'https://open.larksuite.com/open-apis/bitable/v1/apps/{self.base_token}/tables/{table_id}/records/batch_create'

        records = [ {'fields': {col: row[col] for col in df.columns}}
                     for row in df.to_dict(orient='records') ]

        total = len(records)
        num_batches = math.ceil(total / batch_size)

        for i in range(num_batches):
            batch = records[i * batch_size: (i + 1) * batch_size]
            payload = {'records': batch}

            for attempt in range(max_retries):
                res = requests.post(url, headers=self.header, json=payload)
                data = res.json()

                if data.get("code") == 0:
                    print(f'Uploaded batch {i+1}/{num_batches}')
                    break
                else:
                    print(f"Retry {attempt+1} for batch {i+1}: {data}")
                    if attempt < max_retries - 1:
                        time.sleep(1.5)
                    else:
                        raise Exception(f'Lark upload failed: {data}')

            time.sleep(0.2)
    
        print('bq lark completed.')