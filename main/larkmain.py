from pipelines.larkpipelines import CRM_DB, DB_CRM

if __name__ == '__main__':
    CRM_DB().full_lark_to_db()
    DB_CRM().full_db_to_lark()