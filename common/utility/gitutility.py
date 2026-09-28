import requests

class GitRequest:
    def __init__(self, client ):
        self.client = client
        self.header = self.client.get('header')
        self.owner = self.client.get('owner')
        self.repo = self.client.get('repo')

    def get_runner_list(self): 
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/actions/runs"
        
        params = {
                  "per_page": 100
                 }
                 
        response = requests.get(url, headers=self.header, params=params)
        #response.raise_for_status()
        
        if response is None or not response.json()['workflow_runs']:
            return {}, []

        response = response.json()
        runs = response["workflow_runs"]
        
        return runs, [run["id"] for run in runs]
        
    def get_run_timing(self, run_id):
        path = f'https://api.github.com/repos/{self.owner}/{self.repo}/actions/runs/{run_id}/timing'

        params = { "per_page" : 100 }
        
        response = requests.get(path, headers=self.header, params=params)
        response.raise_for_status()

        response = response.json()

        if response is None or not response.get( 'billable' ):
            return {}
        
        return response

        
