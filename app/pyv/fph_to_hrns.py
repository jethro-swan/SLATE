#!/home/john/NESTS/SLATE/venv/bin/python3
#!/usr/bin/env python3
import os
import sys
#from app.core.slate_core import identify_entity, get_entity_type
from app.core.common import nshash
from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

#ips = sys.argv[1]

script_name = sys.argv[0].delete(".py")
if script_name == "fph_to_hrns":
    fph = sys.argv[1]
    print(fph_to_hrns(fph))
elif script_name == "hrns_to_fph":
    hrns = sys.argv[1]
    fph = nshash(hrns)
    if fph_to_hrns(fph) == hrns:
        print(fph)
    else:
        print("")
