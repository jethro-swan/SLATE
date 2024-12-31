#!/usr/bin/env python3

# This script can be run to (re)initialize the SLATE installation at any time.
# Any existing DBM maps and SQLite databases will be backed up first.

from app.fph_hrns_maps import create_maps, fph_to_hrns
from app.slate_core import create_entities_db
from app.slate_session import create_slate_session_db
from app.slate_seed import create_seed_entities, create_quasitld_set

create_maps()
create_entities_db()
create_slate_session_db()
create_seed_entities()
tld_fph_list, errors = create_quasitld_set(False)

print("The following seed entities have been created (HRNS):")
print("\tseed namespace  = \"global\"")
print("\tseed currency   = \"hours.global\"")
print("\tseed primid     = \"gaia.global\"")
print("\tseed account    = \"hours.gaia.global\"")
