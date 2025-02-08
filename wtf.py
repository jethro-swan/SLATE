#!/home/john/NESTS/SLATE/venv/bin/python3

import sqlite3
from app.core.slate_core import identify_entity, get_entity_type
from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph
from app.core.common import nshash

ENTITIES_DB = "/var/slate/active/db/entities.db"

with sqlite3.connect(ENTITIES_DB) as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT entity_fph, entity_type
        FROM entities_common
        """
    )
    results = cursor.fetchall()
    cursor.close()
if results is not None:
    for result in results:
        print(result)
        entity_fph = result[0]
        entity_type = result[0]
        print(entity_fph + " >>> " + fph_to_hrns(entity_fph) + " :: " + entity_type)
        if nshash(fph_to_hrns(entity_fph)) != entity_fph:
            print("mismatch")
        else:
            print("consistent FPH")
            



