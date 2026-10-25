from config.config import get_json

lark = get_json('lark_report_tables.json')
if lark is None:
    raise KeyError( 'lark_report_tables.json is not in load range' )

BASE_TOKEN = lark.get('BASE_TOKEN') 

report = lark.get('REPORTS')
SALARY = report.get('Salary Table')
EMPLOYEE = report.get( 'Employee Table' )
GIT_REPORT = report.get('Workflow Table')