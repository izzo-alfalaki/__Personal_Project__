"""
git clirnt, this client use free-grained token from github developer consiole, 
this client works on github RESTS API, in this method, we wil return a package

similar to gcp client, it is centralize and purposely given a 'source-of-truth' position

the idea is, 
 *1: COLLECT ALL SECRETS FROM CONFIG -> 2: CREATE A HEADER IN POST/GET METHIOD ____
                                                                                   |
                                        3: UNPACKAGE THEM ORCHESTRATION LAYER <____|*
"""

from config.gitconfig import *

class GitClient:
    """
    similar to gcpclient, this class is one-to-one connection to github, heres the thing:
    one token / app only accessible to one account, so thats mean to stimulate many account together with repo(S), 
    we need to re-create the function such that GitClient will ask / require for self.token at 
    orchestration layer
    """
    def __init__(self, repo_name = None, owner_name = None) -> dict:
        self.token = token

        # repo_name is stimulate-able, which mean one app from account izzo@gmail.com, can charhges all 
        # repo owned by izzo@gmail.com
        if repo_name is None or owner_name is None:
            self.repo_name = repo
            self.owner_name = owner
        else:
            self.repo_name = repo_name
            self.owner_name = owner_name
    
    def declare(self) -> dict:
        header = {
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json"
                 }
        return dict(zip(['header', 'repo', 'owner'] , [  header, self.repo_name, self.owner_name  ]))