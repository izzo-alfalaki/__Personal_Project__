from config.config import get_json

lark = get_json('lark_report_table.json')

BASE_TOKEN = lark.get('BASE_TOKEN') 

report = lark.get('REPORTS')
GIT_REPORT = report.get('GIT_REPORT')
TEST_REPORT = report.get( 'TEST_REPORT' )
IZZO_TABLE = report.get('IZZO_TABLE')