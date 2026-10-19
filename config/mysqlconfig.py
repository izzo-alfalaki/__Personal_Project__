"""
unloading packages, 
 besides of blindly ckeck for packages, i usallay went throhg a quick 
 check. just in case any of config is missing, 

 when we found out which one of them is missing then we can fix it quickly, 
"""
from config.config import get_json
main = get_json('mysql')
main = main["packages"]

def check():
    packages = [p for p in main.keys()]
    if not packages:
        # we can force early break instead of failing at Loading stage to db
        # raise Exception("no packages found in mysql config") / or pass it
        print("no packages found in mysql config")
        pass

    # on running, i wont use any of IZZO or another IZZO, 
    # but best to pass config_lib instead
    config_lib = {}
    for p in packages:
        meta = main.get('packages', None ).get(p, None)
        config_lib[p] = meta

    IZZO = config_lib.get('izzo', None)
    ANOTHER_IZZO = config_lib.get('another_izzo', None)

    return IZZO, ANOTHER_IZZO