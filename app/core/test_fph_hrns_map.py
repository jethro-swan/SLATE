#!/usr/bin/env python3

# This is a temporary test file for the FPH<>HRNS mapping.
# It has shown almost all of the functions below to be working as expected ...

import random
import string
from faker import Faker

from constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR
from constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from constants import FNAME_DATETIME_FMT
#from common import hrns_to_fph, fph_to_hrns
#from fph_hrns_maps import create_maps, hrns_to_fph, fph_to_hrns
#from common import dbm_fetch, dbm_store
from fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from common import nshash
from common import filename_timestamp as timestamp
#from slate_core import create_maps
from regexp_list import re_fph, re_hrns
#from test import random_hrns, fake_hrns

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

print()
print("Some randomly-generated HRNS fakes and their corresponding FPH:")
print()

N = 100
l_fph = []
l_hrns = []

for n in range(N):
    hrns = fake_hrns()
    l_hrns.append(hrns)
    fph, m = hrns_to_fph(hrns)
    l_fph.append(fph)
    print("\t" + fph + " :: " + hrns)

print()
print("The same HRNS fakes retrieved from the FPH>HRNS map:")
print()

l2_hrns = []
for fph in l_fph:
    hrns_ = fph_to_hrns(fph)
    l2_hrns.append(hrns_)
    print("\t" + fph + " :: " + hrns_)
#    print(hrns_)

print()
print("Comparing the set of retrieved HRNS fakes with the generated set:")

mismatch_found = False
for hrns in l_hrns:
    if not hrns in l2_hrns:
        print("\tMismatch: " + hrns)
        mismatch_found = True
if not mismatch_found:
    print("\tNo mismatch found")

print()
