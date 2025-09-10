#!/home/slate/SLATE/venv/bin/python3

from app.core.configdb import create_config_db
from app.core.configdb import get_config
from app.core.configdb import delete_config_key_from_map
from app.core.configdb import set_config
from app.core.configdb import read_config_file_to_db
from app.core.dbm_functions import dbm_keys
from app.core.constants import CONFIG_MAP



create_config_db()

read_config_file_to_db()

for k in dbm_keys(CONFIG_MAP):
    print(k + " : " + str(get_config(k)))

print()

    #get_config("show_dataset_csv_import_link")



#delete_config_key_from_map(config_key)

#set_config(config_key, config_value)

#get_config(config_key)
