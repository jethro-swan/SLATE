#!/home/slate/SLATE/venv/bin/python3

from app.core.flags import create_flag_db
from app.core.flags import get_flag
from app.core.flags import delete_flag_key_from_map
from app.core.flags import set_flag, unset_flag
from app.core.dbm_functions import dbm_keys
from app.core.constants import FLAG_MAP



#create_flag_db()

def list_flags():
    for k in dbm_keys(FLAG_MAP):
        print(k + " : " + str(get_flag(k)))
    print()

flags = ["allow_queued_imports", "run_robots", "run_hub_sych"]

print()
list_flags()
for flag in flags:
    set_flag(flag)
    list_flags()
for flag in flags:
    unset_flag(flag)
    list_flags()
delete_flag_key_from_map("run_imports")
for flag in flags:
    set_flag(flag)
    list_flags()
