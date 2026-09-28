from config.config import get_json

lark = get_json('lark.json')

APP_ID = lark.get('APP_ID')
APP_SECRET = lark.get('APP_SECRET')