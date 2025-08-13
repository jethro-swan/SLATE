#!/home/slate/SLATE/venv/bin/python3

# This script can be run to (re)initialize the SLATE installation at any time.
# Any existing DBM maps and SQLite databases will be backed up first.

from app.core.fph_hrns_maps import create_maps
from app.core.fph_hrns_maps import fph_to_hrns
from app.core.fph_hrns_maps import hrns_to_fph
from app.core.slate_core import create_entities_db
from app.core.slate_session import create_slate_session_db
from app.core.slate_core import create_hubs_db
from app.core.payments import create_payments_db
from app.core.messaging import create_messages_db
from app.core.slate_seed import create_seed_entities
from app.core.slate_seed import create_quasitld_set
from app.core.slate_seed import create_substrate
from app.core.constants import SLATE_LOGS
from app.core.constants import SLATE_LOGS_BKP_DIR
from app.core.constants import DEBUG_LOG
from app.core.constants import ERROR_LOG
from app.core.constants import AUTH_LOG
from app.core.constants import ACTIVITY_LOG

from app.core.slate_core import new_namespace
from app.core.slate_core import new_currency
from app.core.slate_core import split_hrns

print("creating DBM maps")
create_maps()
print("creating entities databases (SQLite)")
create_entities_db()
print("creating session databases (SQLite)")
create_slate_session_db()
print("creating seed entities")
create_seed_entities()
print("creating payments databases (SQLite)")
create_payments_db()
print("creating hubs databases (SQLite)")
create_hubs_db()
print("creating messages databases (SQLite)")
create_messages_db()

create_substrate()

print("creating quasi-TLD root namespace set")
tld_fph_list, errors = create_quasitld_set(False)
#print(errors)
#print(tld_fph_list)
#for n_fph in tld_fph_list:
#    print(fph_to_hrns(n_fph))

print("\n\nThe following seed entities have been created (HRNS):")
print("\tseed namespace  = \"cc\"")
print("\tseed currency   = \"cc\"")
print("\tseed primid     = \"cc\"")
print("\tseed account    = \"cc.adm.cc\"")
print()
print(
    "You will be able to log in as the initial administrator (the seed " \
    + "identity) using the following details:"
)
print("\tusername = adm.cc")
print("\tpassword = Gl0balM3ltd0wn")
print("\tPIN      = 123456")
print()

# 2025-05-30
# Create the following seed *currencies* with  adm.cc  as the initial steward.
steward_fph, m = hrns_to_fph("adm.cc")
clist = ["kwh.cc", "hrs.cc"]
for c in clist:
    cname, c_parent_ns_hrns = split_hrns(c)
    parent_namespace_fph, m = hrns_to_fph(c_parent_ns_hrns)
    currency_fph, \
    currency_hrns, \
    m = new_currency(
            cname,
            parent_namespace_fph,
            steward_fph,
            "",
            "",
            "cname"
        )
    if m:
        print(m)
