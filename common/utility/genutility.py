"""
Welcome to data-generation as Json forms. In this pipelines we will demonstrate:
# 1 - GENERATE RANDOM DATA
# 2 - Using JSON_PARSE_DATA and Load it to bcket-system
# 3 - Union Json_PARSE_DATA and Append all as tables
# 4 - Model the uinion-table
This generated data is a `TRANSACTION DATA` of an retail, my goals is after appending and union data
we want to study order list / product pick *significant to see*:
(1) Customer Movement
(2) Product Relational
(3) Customer Behaviour 
This significant can help us to construct an example of store-cabinet management, or Pricing Strategy and much more.
"""
import os
import json
import random
import string
import pandas as pd
from datetime import datetime, timedelta

def GenSchema() -> pd.DataFrame : 
    """
    Before hand, I create an appendix, in order to make sure generated data can be seem :
    structured and relational **while at the same time** varies within 
    (1) date, (2) transaction_id, and any else.
    """
    parent = 'config'
    sub = 'appendix.json'
    
    if os.path.exists( parent ):
        if sub in os.listdir( parent ): 
            with open( f'{parent}/{sub}', 'r') as file:
                all = json.load( file )
            
            return pd.DataFrame( all['res'] )

    all = { 
            "res" : []
        }
    
    smoother = 0.01
    for i in range( 1, 201 ):
        scheme = {}
            
        names = []
        for _ in range(1, random.randint( 3, 5 ) ):
            names.append(random.choice( string.ascii_letters))
    
        scheme_name = ''.join( names ).upper()
    
        scheme["id"] = i
    
        if i <= 30:
            scheme['category'] = "Category A"
            scheme['price'] = random.randint( 20, 50) - smoother 
        elif i > 30 and i <= 50:
            scheme['category'] = "Category B"
            scheme['price'] = random.randint( 50, 70) - smoother
        elif i > 50 and i <= 70:
            scheme['category'] = "Category C"
            scheme['price'] = random.randint( 1, 30) - smoother
        elif i > 70 and i <= 120:
            scheme['category'] = "Category D"
            scheme['price'] = random.randint( 60, 100) - smoother
        elif i > 120 and i <= 160:
            scheme['category'] = "Category E"
            scheme['price'] = random.randint( 20, 80) - smoother
        elif i > 160 and i <= 180:
            scheme['category'] = "Category F"
            scheme['price'] = random.randint( 10, 30) - smoother
        else:
            scheme['category'] = "Category E"
            scheme['price'] = random.randint( 1, 10) - smoother
    
        scheme['name'] = scheme['category'].replace(' ', '_').upper() + '-' + scheme_name + str( i )
    
        all['res'].append( scheme )
    
    #print( all )
                
        with open( f'{parent}/{sub}', 'w') as file:    
            json.dump( all, file, indent=4)

    
    print( 'write-complete')
    df = pd.DataFrame( all['res'] )
    print( df )
    return df

def gen_date():
    """
    Date Generating, to replicate response-type, we use unix timestamp
    """
    x = datetime(2026, 1, 1, 0, 0, 0)
    xt = datetime.now()

    total_seconds = int( (xt - x).total_seconds() )
    random_x = x + timedelta( seconds=random.randint( 0, total_seconds ) )

    random_x = random_x.timestamp()
    #test = pd.to_datetime( random_x, unit='s')   
    return random_x

class GenerateWorkingTools:
    """
    # The major topic is item list, *a picked-item list* and *returned-item list*, where both of them 
    # will decide how other data will behave accroddibgly.
    ## Therefore 
    ## this function pretty much about generating 'Working Tools'
    """
    def __init__(self):
        self.smoothing = 6

    def confirmed_item( self ) -> list:
        items = []    
        item = 0
        
        while item < 200:
            y = random.randint(1, self.smoothing * 10 )
            
            item = item + y

            if item > 200:
                break

            items.append( item )

        return items

    def return_item( self, confirmed_item : list ) -> tuple:
        return_list = []

        if len(confirmed_item) - 1 <= 0:
            return return_list, confirmed_item
        
        for _ in range( 1, len( confirmed_item ) + self.smoothing ):
            
            val = random.randint( 1, 200 )

            if val in confirmed_item:
                return_list.append( val ) 
            
        return return_list, [ c for c in confirmed_item if c not in return_list ]

    def generate_item( self ):
        returned, confirmed = self.return_item( self.confirmed_item() )
        return returned, confirmed 

class WorkingList:
    def __init__(self, schema, notbasket, basket):
        """
        Once working tools is initialized, then we can pass it to stimulator.
        At this point, we need to make sure WorkingTools is no longer a variable but constant, 
        This aim to make sure other assigned / rand variable will sit still and depend on same SOT
        """
        self.schema = schema
        self.notbasket = notbasket
        self.basket = basket

    def get_list_price( self ):
        """
        # Non-basket, basket
         
        x, y = generate_item()
        a, b = get_list_price( x, y )

        print( a ) 
        print( b )
        """        
        echo_list = []

        for x in [  self.notbasket, self.basket  ]:
            if not x:
                final_list = []
            
            x = { 'id' : x }
            x = pd.DataFrame( x )
            x = pd.merge( x, self.schema[['id', 'price']], on= 'id')

            final_list = x['price'].tolist()
            
            echo_list.append( final_list )
        
        return echo_list[0], echo_list[1] 

    def get_list_quantity( self ):
        """
        # Non-basket, basket
        """
        qone = self.basket 
        qnot = self.notbasket

        q = []
        for _ in range( 1, len(qone) + 1 ):
            q.append( random.randint( 1, 10 ) )

        qnon = []
        for _ in range( 1, len(qnot) + 1 ):
            qnon.append( random.randint( 1, 5 ) )

        return qnon, q

    def get_total( self, discount : float ):
        nonbasket, basket = self.get_list_price()
        qnon, q = self.get_list_quantity()

        all_total = 0
        for x, y in zip( basket, q ):
            total = x * y

            all_total += total

        if discount == 0:
            return nonbasket, basket, qnon, q, all_total
        
        return nonbasket, basket, qnon, q, all_total * ( 1 - ( discount / 100 ) ) 

    def get_member_id( self ):
        if random.randint(1, 649) <= 276:
            year = random.randint( 2020, 2026 )  
            unid = random.randint( 1000, 2763 ) 
            return f"{year}{unid}"
        else:
            return ""

    def get_all( self ):
        """
        Finally generating all data, concept # Generate Value --> Freeze Value --> Write Value
        """
        ismember = self.get_member_id()

        if ismember:
            nonbasket, basket, qnon, q, prices = self.get_total( discount=random.randint( 1, 25 ) )
        else:
            ismember = ""
            nonbasket, basket, qnon, q, prices = self.get_total(  discount = 0 )

        return nonbasket, basket, qnon, q, prices, ismember

