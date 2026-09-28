from config.gitconfig import *

class GitClient:
    def __init__(self, repo_name = None, owner_name = None) -> dict:
        self.token = token
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