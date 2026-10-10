"""
my config system:

my config was stored in json, and all config json was added to .gitignore

when unning on local / vscode, i can call, load and read upon json files
most of the time, my json files comes as non single valie, but like dictionary:

namely: 
larkconfog.py

{ 
  'base_token_A' : {
        'token' : '***',
        'all_table' : {
                        'table_a' : '***', 
                        'table_b' : '***',
                        'table_c' : '***'
                    }
                    ,
        'all_view' : {
                        'view_a' : '***', 
                        'view_b' : '***',
                        'view_c' : '***'
                    }
    },

  'base_token_B' : {
        'token' : '***',
        'all_table' : {
                        'table_a' : '***', 
                        'table_b' : '***',
                        'table_c' : '***'
                    }
                    ,
        'all_view' : {
                        'view_a' : '***', 
                        'view_b' : '***',
                        'view_c' : '***'
                    }
    }
}

using this json. we will un-pack it at mainconfig.py
namely;

  with open( 'path/json', 'r' ) as f:
    config = json.load( f )

  then let say we need can assign config as 

base_tokena config ...

"""

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