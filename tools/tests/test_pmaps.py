#!/home/slate/SLATE/venv/bin/python3

import sqlite3
#from app.core.slate_core import register_identifier
#from app.core.slate_core import get_entity_types
#from app.core.slate_core import set_entity_type
#from app.core.slate_core import register_full_entity_set
#from app.core.slate_core import register_entity_type
#from app.core.slate_core import deregister_entity_type
#from app.core.slate_core import identify_entity
#from app.core.slate_core import new_primid
#from app.core.slate_core import new_account
#from app.core.slate_core import new_pairing
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
