#!/usr/bin/env python3

# This script can be run to (re)initialize the SLATE installation at any time.
# Any existing DBM maps and SQLite databases will be backed up first.

from app.core.fph_hrns_maps import create_maps, fph_to_hrns
from app.core.slate_core import create_entities_db
from app.core.slate_session import create_slate_session_db
from app.core.slate_core import create_hubs_db
from app.core.payments import create_payments_db
from app.core.messaging import create_messages_db
from app.core.slate_seed import create_seed_entities, create_quasitld_set

create_maps()
create_entities_db()
create_slate_session_db()
create_seed_entities()
create_payments_db()
create_hubs_db()
create_messages_db()
tld_fph_list, errors = create_quasitld_set(False)

print("The following seed entities have been created (HRNS):")
print("\tseed namespace  = \"cc\"")
print("\tseed currency   = \"hrs.cc\"")
print("\tseed primid     = \"adm.cc\"")
print("\tseed account    = \"hrs.adm.cc\"")
print()
print(
    "You will be able to log in as the initial administrator (the seed " \
    + "identity) using the following details:"
)
print("\tusername = adm.cc")
print("\tpassword = Gl0balM3ltd0wn")
print("\tPIN      = 123456")
print()
