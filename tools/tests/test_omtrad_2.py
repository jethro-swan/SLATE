#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import pickle
import random

from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

from app.core.slate_core import new_namespace, new_currency, new_primid
from app.core.slate_core import split_hrns

from app.core.omtrad import *


parent_fph, m = hrns_to_fph("bb.cc")
if m:
    print(m)
print(parent_fph + " > " + fph_to_hrns(parent_fph))

currency_fph, m = hrns_to_fph("cc")
if m:
    print(m)
print(currency_fph + " > " + fph_to_hrns(currency_fph))

primid_fph, m = hrns_to_fph("bb.cc")
if m:
    print(m)
print(primid_fph + " > " + fph_to_hrns(primid_fph))

c_hrns = "hrs.bb.cc"

# Create a new *namespace* "zz.bb.cc":
#ns_fph, ns_hrns, m = new_namespace("zz", parent_fph, currency_fph, primid_fph)
#if m:
#    print(m)
#print(ns_fph + " > " + ns_hrns)

# Create a new *currency* "hrs.bb.cc":
#c_fph, c_hrns, m = new_currency("hrs", parent_fph, primid_fph, "", "", "hrs")
#if m:
#    print(m)
#print(c_fph + " > " + c_hrns)

ahid_hrns_list = []
for i in range(0,200):
    ahid_name = "ah" + str(i).zfill(3)
    ahid_hrns = ahid_name + ".bb.cc"
    p_fph = create_new_pairing(primid_fph, ahid_hrns, c_hrns)
    ahid_hrns_list.append(ahid_hrns)
#    print(p_fph)

#pmap, m = retrieve_pmap("bb.cc")

for n in range(300):
    payer_ahid_hrns = random.choice(ahid_hrns_list)
#    print(payer_ahid_hrns)
    payee_ahid_hrns = random.choice(ahid_hrns_list)
#    print(payee_ahid_hrns)
    amount = random.randint(0, 100000)
    annotation = "test B" + str(n)
    if payer_ahid_hrns != payee_ahid_hrns:
        print(
            c_hrns + " : " \
            + payer_ahid_hrns + " > " + payee_ahid_hrns \
            + " | " + str(amount) \
            + " | " + annotation
        )
        m = ah_payment(
                payer_ahid_hrns,
                payee_ahid_hrns,
                c_hrns,
                amount,
                annotation
            )
        if m:
            print(m)
print()
