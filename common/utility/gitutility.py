"""
This is integration layer:
Integrating between GitHub to platform of choices.
Gitrequests expect client from GitClient, if we had multi client, we can build them seperately at
orchestrations layers. this class similarly to big query class, was used to pull data, and 
more * if we decide to create more udf *

not much of a 'value' from the data, sicne its only Git-actions historical-run record. 
but, key point: was to demonstrate
RESTS API skills. maybe we do some actual value of data pull further , todays date: 2026-10-08 
"""
import requests

class GitRequest:
    """
    this class purely handle response, none of dataframes, 
    """
    def __init__(self, client ):
        self.client = client
        self.header = self.client.get('header')
        self.owner = self.client.get('owner')
        self.repo = self.client.get('repo')

    def pull( self, url ):
        """
        ive got couple refrences from git docuemtation, also, i find a way to genrealize the paginantion
        params, so instead of checking like if len( res['id']  ) > 100 then break, we use response.links

        references:
         - params / header:
            https://docs.github.com/en/rest/actions/workflow-runs
            https://docs.github.com/en/rest/actions/workflow-runs

         - pagination:
            https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api
        """
        all_response = []
        params = {
            'per_page' : 100
        }

        page = 1
        while True:
            params['page'] = page
            response = requests.get( url, headers = self.header, params=params  )

            response.raise_for_status()
            res_data = response.json()

            if res_data.get('errors'):
                break

            all_response.append( res_data )

            if 'last' in response.links or 'next' not in response.links:
                break

            page += 1

        # i usually test local and read response just to get whats whole respomnse look like,
        # then we can play with page paginantion

        #import json    
        #with open("response_data.json", "w", encoding="utf-8") as f:
        #        json.dump(response, f, ensure_ascii=False, indent=4)    

        return all_response

    def get_runner_list(self):
        """
        pull data of runner
        """
        url = f'https://api.github.com/repos/{self.owner}/{self.repo}/actions/runs'
        all_response = self.pull( url )

        return all_response
        
    def get_run_timing(self, run_id):
        """
        pull run / actions metrics. this func use run_id from get_runner_list, we can use 
        for id ina all parsed response of runner
        """
        url = f'https://api.github.com/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/timing'
        all_response = self.pull( url )

        return all_response
