#!/home/slate/SLATE/venv/bin/python3

import sqlite3
from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.constants import ENTITIES_DB
from app.core.slate_core import retrieve_pmap



with sqlite3.connect(ENTITIES_DB) as conn:
    cursor = conn.cursor()
    cursor.execute(
        "SELECT entity_fph, pmap FROM primids"
    )
    results = cursor.fetchall()
cursor.close()
if results is not None:
    for r in results:
        primid_fph = fph_to_hrns(r[0])
        pmap, m = retrieve_pmap(primid_fph)
        print("\nprimid = " + primid_fph + " :: pmap = ", end="")
        #print("pmap = ", end="")
        print(pmap)
    print()
