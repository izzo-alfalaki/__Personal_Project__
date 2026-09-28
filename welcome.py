import os

def main():
    """
    1) make common --> room for utility and connection
    2) make config 
    2) make pipelines --> for structuring 'import from utility + import from connection'
    3) make entry gate, - where to execute the pipelines
    4) make .github for yaml
    4) make log / necessary 
    5) make sql

    overall structure 

    D:/izzo/this_repo
                    |_ .guthub
                    |        |_ workflows
                    |_ config
                    |_ sql
                    |_ common
                    |        |_ connection @ client
                    |        |_ utility
                    |_ pipelines
                    |          |_ pipleines for workflow A
                    |          |_ pipleines for workflow B
                    |          |_ pipleines for workflow C
                    |          |_  ... 
                    |_ main @ execute : if __name__ == __main__: main()
                                                                    |_ workflow A
                                                                    |_ workflow B
                                                                    |_ workflow C
                                                                    |_ ... 
    """
    depend = [  '.github', 
                'config',
                'sql',
                'common',
                'pipelines',
                'main', ] 
    
    for x in depend:
        if x == '.github':
            os.makedirs( x, exist_ok=True)
            os.makedirs( f'{x}/workflows' , exist_ok=True )
        elif x == 'common':
            os.makedirs( x, exist_ok=True)
            os.makedirs( f'{x}/utility' , exist_ok=True )
            os.makedirs( f'{x}/connection' , exist_ok=True )    

        else:
            os.makedirs( x, exist_ok=True)

    gitignore =\
"""# Byte-compiled / optimized / DLL files
__pycache__/
*$py.class
                               
# Virtual Environments
venv/
.venv

# Environment variables / secrets
.env"""

    requirement =\
"""pandas>=2.0.3
google-cloud-bigquery>=3.10.0
google-api-python-client>=2.90.0
google-auth>=2.21.0
pyarrow>=10.0.0

gspread
gspread-dataframe
pandas-gbq
db-dtypes
openpyxl"""
    
    for x, y in zip(['.gitignore', 'requirements.txt'], [ gitignore, requirement ]):
        with open(x, "w") as f:
            f.write(y.strip())

if __name__ == '__main__':
    main()