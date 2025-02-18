#!/home/john/NESTS/SLATE/venv/bin/python3
#!/usr/bin/env python3

# This is a temporary test file for the FPH<>HRNS mapping.
# It has shown almost all of the functions below to be working as expected ...

import random
import string
from faker import Faker

from core.constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR
from core.constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from core.constants import FNAME_DATETIME_FMT
#from common import hrns_to_fph, fph_to_hrns
#from fph_hrns_maps import create_maps, hrns_to_fph, fph_to_hrns
#from common import dbm_fetch, dbm_store
from core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from core.fph_hrns_maps import update_mapping
from core.common import nshash
from core.common import filename_timestamp as timestamp
#from slate_core import create_maps
from core.regexp_list import re_fph, re_hrns
#from test import random_hrns, fake_hrns

from core.display import thin_line, thick_line, title_line, thin_title_line
from core.display import yN, Yn, get_cli_number_input, pause


# ... but, for reasons not yet identified at 2024-08-25, importing from test.py
# creates havoc via slate_core.py

#------------------------------------------------------------------------------
# (Copied from test.py rather than imported.)

def random_name():
    name_length = random.randint(3,7)
    letters = string.ascii_lowercase
    n = []
    for i in range(name_length):
        n.append(random.choice(letters))
    return "".join(n)

def random_hrns(length):
    hrnsbits = []
    for i in range(length):
        hrnsbits.append(random_name())
    return ".".join(hrnsbits)

def fake_hrns():
    return random_hrns(random.randint(1,8))

#------------------------------------------------------------------------------

create_maps()

print("\nSome randomly-generated HRNS fakes and their corresponding FPH:\n")

N = get_cli_number_input(
        "How many fake HRNS should be created? ",
        50, 500, 100
    )


#N = 1000
l_fph = []
l_hrns = []

for n in range(N):
    hrns = fake_hrns()
    l_hrns.append(hrns)
    fph, m = hrns_to_fph(hrns)
    l_fph.append(fph)
    print("\t" + fph + " < " + hrns)

thin_line()
pause()
print("\nThe same HRNS fakes retrieved from the FPH>HRNS map:\n")

l2_hrns = []
for fph in l_fph:
    hrns_ = fph_to_hrns(fph)
    l2_hrns.append(hrns_)
    print("\t" + fph + " > " + hrns_)

thin_line()
pause()
print("\nComparing the set of retrieved HRNS fakes with the generated set:\n")
#pause()

mismatch_found = False
for hrns in l_hrns:
    if not hrns in l2_hrns:
        print("\tMismatch: " + hrns)
        mismatch_found = True
if not mismatch_found:
    print("\tNo mismatch found")

thin_line()
pause()
print("\nTesting map updating:\n")

entity_new_hrns = fake_hrns()
entity_current_fph = random.choice(l_fph)
entity_current_hrns = fph_to_hrns(entity_current_fph)
print("\tcurrent mapping: " + entity_current_fph + " > " + entity_current_hrns)
update_mapping(entity_current_hrns, entity_new_hrns)
print("\tUpdated mapping: " + entity_current_fph + " > " + entity_new_hrns)
test_fph, m = hrns_to_fph(entity_new_hrns)
if m:
    print(m)
if fph_to_hrns(test_fph) == entity_new_hrns:
    print("\tRe-mapping successful")

print()
thin_line()
