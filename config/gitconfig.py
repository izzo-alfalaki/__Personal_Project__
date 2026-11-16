from config.config import get_json

res = get_json('git.json')

token = res.get('token', None)
repo = res.get('repo', None)
owner = res.get( 'owner', None )