import os
import json
    
root = 'config/'

def get_path(  what:str ) -> str: 
    if what.endswith('.json'):
        x = what
    else:
        x = f'{what}.json'
    
    where = f'{root}{what}' 
    if os.path.exists( where ):
        return where

    return f'path error for {x}'

def get_json(  what: str ) -> json:
    if not what.endswith( '.json'):
        x = f'{what}.json'
    else:
        x = what

    git = os.path.join(root, x)
    if os.path.exists(git):
        with open(git, "r") as f:
            return json.load(f)