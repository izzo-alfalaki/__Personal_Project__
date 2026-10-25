import os
# i am alos familiar with load env method
# but as all, we will need all new structure and logic where i didnt
# demonstrate, it was the classic .env method anyway 
packages = os.getenv("MYSQL_USER", {})

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from urllib.parse import quote_plus
from config.mysqlconfig import main
"""
        this is mysql connection, here, we commit to create an engine, and
        namely we had many users, so we design this functionn such that it 
        varies across many users, and even varies across database for one users
        
        user package is wrapped in json configiration -> kept into config + .gitignore and
        in cloud-environment, we use secret manager.

        ** FROM CONFIG, WE EXPECT SUCH AS CONFIG_LIB.get('izzo') or maybe
        user_package = from cnfig.mysqlconfig import IZZO
        """

class MysqlClient:
    def __init__(self):
        self.load = main 
        if not main:
            self.load = {}

    def connection( self, 
                    user_package: str  = None, 
                    database : str  = None  ) -> str:

        if user_package not in [ p for p in self.load.keys() ]:
            raise KeyError( f'no such user : {user_package}' )
                
        if not self.load:
            raise ValueError( 'passed packages is none: empty.dictionary' )
        config = self.load.get( user_package )

        self.user = config.get("MYSQL_USER", "root")
        host = config.get("MYSQL_HOST", "localhost")
        port = config.get("MYSQL_PORT", "3306")        
        
        password = config.get("MYSQL_PASSWORD", None)
        password = quote_plus(password)
        if password is None:
            return print( 'confoguration faild: no password passed' )
        
        self.dbkey = config.get("MYSQL_DATABASE").get( database, 'not_found' )
        if database == 'not_found':
            raise KeyError( f'invalid database : {database}' )

        return  f"mysql+pymysql://{self.user}:{password}@{host}:{port}/{self.dbkey}"

    def engine( self, **kwargs ) -> Engine:
        mysql_engine = create_engine(
                self.connection( **kwargs ),
                pool_size=5,  
                max_overflow=10,   
                pool_recycle=3600 
            )
        
        return mysql_engine