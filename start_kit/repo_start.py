import os 

def writes_dags():
    startdir = 'start_kit'
    os.makedirs( startdir, exist_ok=True)
    for f in [ c for c in os.listdir( startdir ) if c.endswith( '.md') and '-dag' in c]:
        with open( f'{startdir}/{f}', 'r') as read:
            x = read.read()

        x = str( x )
        x = x.replace( "```python", "" )
        x = x.replace( "```", "" )
        with open( f'dags/{f.replace( '.md', '.py')}', 'w') as write:
            write.write( x )

def write_init():
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
        
        if 'pycache' in z:
            continue
        
        with open( name, 'w') as file:
            file.write('')
            print( f'created {name}')

writes_dags()
write_init()