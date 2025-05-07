#!/home/slate/SLATE/venv/bin/python3

import os
import sys
#import re
#from app.core.slate_core import identify_entity, get_entity_type
from app.core.common import nshash
from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph
from app.core.slate_core import get_entity_type

script_name = sys.argv[0].replace(".py", "").replace("./", "")
script_name = script_name.replace("/usr/local/bin/", "")

#print(sys.argv[0])
#print(script_name)
#print(sys.argv[1])

if script_name == "fph_to_hrns":
    fph = sys.argv[1]
    etype, m = get_entity_type(fph)
    #print(fph + " >>> " + etype, end="")
#    print(fph, end="")
    if m:
        print(" (" + m + ")")
#    else:
#        print()
    print(fph_to_hrns(fph) + " >>> " + etype)
elif script_name == "hrns_to_fph":
    hrns = sys.argv[1]
#    print(hrns)
    fph_1 = nshash(hrns)
    fph_2, m = hrns_to_fph(hrns)
    if fph_1 != fph_2:
        print("hash mismatch")
    if fph_to_hrns(fph_2) == hrns:
        etype, m = get_entity_type(fph_2)
        print(fph_2 + " >>> " + etype, end="")
        if m:
            print(" (" + m + ")")
    else:
        print("")
    print("")
