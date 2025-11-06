#!/home/slate/SLATE/venv/bin/python3

import shutil

# This script can be run to (re)initialize the SLATE installation at any time.
# Any existing DBM maps and SQLite databases will be backed up first.

from app.core.fph_hrns_maps import create_maps
from app.core.fph_hrns_maps import fph_to_hrns
from app.core.fph_hrns_maps import hrns_to_fph

from app.core.slate_core import create_identifiers_db
from app.core.slate_core import create_entities_db
from app.core.slate_core import create_hubs_db
from app.core.slate_core import new_namespace
from app.core.slate_core import new_currency
from app.core.slate_core import split_hrns

from app.core.slate_session import create_slate_session_db

from app.core.payments import create_payments_db

from app.core.messaging import create_messages_db

from app.core.slate_seed import create_seed_entities
from app.core.slate_seed import create_quasitld_set
from app.core.slate_seed import create_substrate
from app.core.slate_seed import create_sandbox_space

from app.core.constants import SLATE_LOGS
from app.core.constants import SLATE_LOGS_BKP_DIR
from app.core.constants import DEBUG_LOG
from app.core.constants import ERROR_LOG
from app.core.constants import AUTH_LOG
from app.core.constants import ACTIVITY_LOG
from app.core.constants import CONFIG_MAP
from app.core.constants import FPH_PARENT_MAP
from app.core.constants import DATA
from app.core.constants import BACKUPS

from app.core.unix_functions import create_dir
from app.core.unix_functions import treecopy
from app.core.unix_functions import fcopy
#from app.core.unix_functions import fcopysl

from app.core.common import filename_timestamp

from app.core.dbm_functions import dbm_keys

from app.core.configdb import create_config_map
from app.core.configdb import read_config_file_to_map
from app.core.configdb import get_config

from app.core.flags import create_flag_db

from app.core.robots import create_robots_db
from app.core.robots import create_robots


# The hub configuration map is populated from the ~/hub_config file.
create_config_map()
read_config_file_to_map()
# The configuration values are displayed:
for k in dbm_keys(CONFIG_MAP):
    print(k + " : " + str(get_config(k)))

# The SQLite and DBM files are backed up:
TIMESTAMPED_BACKUP_DIR = BACKUPS + filename_timestamp()
create_dir(TIMESTAMPED_BACKUP_DIR, 0o777)
treecopy(DATA + "/maps", TIMESTAMPED_BACKUP_DIR + "/maps")
treecopy(DATA + "/db", TIMESTAMPED_BACKUP_DIR + "/db")

print("creating DBM maps")
create_maps()
print("creating flags map (DBM)")
create_flag_db()
print("creating identifier entity registration databases (SQLite)")
create_identifiers_db()
print("creating entities databases (SQLite)")
create_entities_db("") # for open/public *namesapce*
print("creating session databases (SQLite)")
create_slate_session_db()
print("creating seed entities")
create_seed_entities()
print("creating payments databases (SQLite)")
create_payments_db("") # for open/public *namesapce*
print("creating hubs databases (SQLite)")
create_hubs_db()
print("creating messages databases (SQLite)")
create_messages_db()
create_substrate()
print("creating robot agents database (SQLite)")
create_robots_db()
print("creating sandbox space")
create_sandbox_space()
print("creating robot agents")
create_robots()

print("creating quasi-TLD root namespace set")
tld_fph_list, errors = create_quasitld_set(False)

# Create the following seed *currencies* with  "cc"  as the initial steward.
steward_fph, m = hrns_to_fph("cc")
clist = ["kwh.cc", "hrs.cc"]
for c in clist:
    cname, c_parent_ns_hrns = split_hrns(c)
    parent_namespace_fph, m = hrns_to_fph(c_parent_ns_hrns)
    currency_fph, currency_hrns, \
    m = new_currency(
            cname,
            parent_namespace_fph,
            steward_fph,
            "",
            "",
            cname,
            "scalar",
            "money",
            "unspecified",
            "lt",
            "unspecified"
        )
    if m:
        print(m)



#create_sandbox_space()
