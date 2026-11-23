import os

def clean_dags():
    if os.path.exists( 'dags' ):
        for f in os.listdir( 'dags'):
            try:
                os.remove( f'dags/{f}')
            except Exception as e:
                print( e )
                print( f'skipping dags/{f}')

    else:
        return

def clean_init():
    parcol = [ f for f in os.listdir( '.' ) if '.' not in f and
                '_' not in f and 'docker' not in f.lower() and 'venv' not in f.lower() ]

    init_list = []
    for par in parcol:
        init_list.append( par )
        
        x = [a for a in os.listdir( par ) if '.' not in a]

        if not x:
            continue

        child = [ par + '/' + b for b in x  ]
        init_list.extend( child )

    print( f'initialize list: {init_list}')
    
    for z in init_list:
        name = f'{z}/__init__.py'

        if 'pycache' in name:
            continue

        try:
            os.remove( name )
            print( f' deleted : {name}')
        except:
            continue

clean_dags()
clean_init()