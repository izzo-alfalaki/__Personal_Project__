from pipelines.gitpipeline import ETL as Git
from pipelines.larkpipeline import ETL as Lark
#from pipelines.genpipeline import ETL as Gen

def main():
    Git().etl()
    Lark().full_lark_to_db()
    #Gen().dump_all_data()

if __name__ == '__main__':
    main()   