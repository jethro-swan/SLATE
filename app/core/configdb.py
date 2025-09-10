import os
import re
from app.core.constants import DB_DIR
from app.core.constants import MAP_BKP_DIR
from app.core.constants import CONFIG_MAP
from app.core.constants import CONFIG
from app.core.common import filename_timestamp as timestamp
from app.core.unix_functions import fcopy
from app.core.dbm_functions import dbm_store
from app.core.dbm_functions import dbm_fetch
from app.core.dbm_functions import dbm_delete
from app.core.dbm_functions import dbm_keys
from app.core.dbm_functions import dbm_create_map

#------------------------------------------------------------------------------
# Create new empty configuration key:value map (run from ~/initialize.py)

def create_config_db():
    # If the databases exists already, this is deleted after a time-stamped
    # copy has been saved.
    T = timestamp()
    if os.path.exists(CONFIG_MAP):
###        fcopy(CONFIG_MAP, MAP_BKP_DIR + 'CONFIG_MAP_' + T + '.dbm')
        os.remove(CONFIG_MAP)
    dbm_create_map(CONFIG_MAP)
    return

#------------------------------------------------------------------------------
# Retrieve constant from configuration key:

def get_config(config_key):
    config_value = dbm_fetch(CONFIG_MAP, config_key).strip()
    if config_value == "FALSE":
        return False
    elif config_value == "TRUE":
        return True;
    else:
        return config_value



#    return dbm_fetch(CONFIG_MAP, config_key).strip()


#def get_list_config_values():


#------------------------------------------------------------------------------

def delete_config_key_from_map(config_key):
    if config_key is None:
        config_key = ""
    config_value = dbm_delete(CONFIG_MAP, fph)
    dbm_delete(CONFIG_MAP, fph)
    return

#------------------------------------------------------------------------------
# Read the hub configuration file (run from ~/initialize.py)

def set_config(config_key, config_value):
    dbm_store(CONFIG_MAP, config_key, config_value)
    return

#------------------------------------------------------------------------------

def read_config_file_to_db():
    re_comment = re.compile(r"^#.*$")
    with open(CONFIG, "r") as cf:
        cflines = cf.readlines()
    for cfl in cflines:
        cfl = cfl.strip()
        if (not cfl) or re_comment.match(cfl):   # comment line or empty line
            continue
        #print(cfl)
        cf = cfl.split(" = ")
        set_config(cf[0], cf[1])

#------------------------------------------------------------------------------
