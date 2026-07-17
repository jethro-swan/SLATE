#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import pickle
import random

from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

from app.core.slate_core import new_namespace, new_currency, new_primid
from app.core.slate_core import split_hrns

from app.core.slate_core import new_pairing
from app.core.slate_core import retrieve_pmap
from app.core.slate_core import complete_parent_namespace
from app.core.payments import ah_payment

parent_fph, m = hrns_to_fph("cc")

primid_fph, m = hrns_to_fph("bb.cc")

nslist = ["uk.cc", "mon.uk.cc", "chep.mon.uk.cc"]
#clist = ["kwh.cc", "hrs.cc", "kwh.uk.cc", "hrs.mon.uk.cc", "h.chep.mon.uk.cc"]
#clist = ["kwh.cc", "hrs.cc", "h.hnrs.cc", "m.hrs.cc", "kwh.uk.cc"]
clist = ["kwh.cc", "hrs.cc", "kwh.uk.cc"]

for ns in nslist:
    nsname, parent_hrns = split_hrns(ns)
    print(nsname + ": " + parent_hrns + "  ", end="")
    parent_fph, m = hrns_to_fph(parent_hrns)
    print(parent_fph + " > " + parent_hrns)

    namespace_fph, namespace_hrns, \
    m = new_namespace(
            nsname,         # name of *namespace*
            parent_fph,     # parent of *namespace*
            "cc",           # default *currency* of *namespace*
            primid_fph      # steward of *namespace*
        )

    print("namespace: " + namespace_fph + " > " + namespace_hrns)
    print()

for c in clist:
    cname, parent_hrns = split_hrns(c)
    print(cname + ": " + parent_hrns + "  ", end="")
    parent_fph, m = hrns_to_fph(parent_hrns)
    print(parent_fph + " > " + parent_hrns)

    currency_fph, currency_hrns, \
    m = new_currency(
            cname,          # name of *currency*
            parent_fph,     # parent of *currency*
            primid_fph,     # steward of *currency*
            "",             # prefix
            "",             # suffix
            "cname",        # default *account* name
            account_type="scalar",
            category="money",
            units="unspecified",
            metrical_equivalence="unspecified",
            dimensions="unspecified"
        )

#    print("currency: " + currency_fph + " > " + currency_hrns)
#    print()

print("="*80)
print("Running test entity identification loop")
print("-"*80)
for ahid_hrns in ["ah1.bb.cc", "ah2.bb.cc", "ah3.bb.cc", "ah4.bb.cc"]:
    for currency_hrns in ["h.hrs.cc", "m.hrs.cc", "hrs.cc", "kwh.cc"]:
        p_fph = new_pairing("bb.cc", ahid_hrns, currency_hrns)
        print(p_fph)
print("="*80)

pmap, m = retrieve_pmap("bb.cc")


complete_parent_namespace("zx.cv.l5.cald.mon.uk", primid_fph)

test_entity_identification = True
test_entity_identification = False

#run_payment_test_loop = False
run_payment_test_loop = True

#display_random_selection = False
display_random_selection = True

#test_payments = False
test_payments = True

ahid_hrns_list = ["ah1.bb.cc", "ah2.bb.cc", "ah3.bb.cc", "ah4.bb.cc"]
currency_hrns_list = ["h.hrs.cc", "m.hrs.cc", "hrs.cc", "kwh.cc"]

if test_entity_identification:
    print("="*80)
    print("Running test entity identification loop")
    print("-"*80)
    for ahid_hrns in ahid_hrns_list:
        ahid_fph, ahid_hrns, etypes, \
        m = identify_entity(ahid_hrns)
        if m:
            print(m)
        if not ahid_fph:
            print(ahid_fph + " is not a registered identifier (18)")
        elif not ("ahid" in etypes):
            print(ahid_hrns + " has no registered ahid")
        print(etype + ": " + ahid_fph + " > " + ahid_hrns)
    for currency_hrns in currency_hrns_list:
        currency_fph, currency_hrns, etypes, \
        m = identify_entity(currency_hrns)
        if m:
            print(m)
        if not currency_fph:
            print(currency_fph + " is not a registered identifier (19)")
        elif not ("currency" in etypes):
            print(currency_hrns + " has no registered  currency")
        print(etype + ": " + currency_fph + " > " + currency_hrns)
    print("="*80)

if run_payment_test_loop:
    print("="*80)
    print("Running payment test loop")
    print("-"*80)
    for n in range(100):
        payer_ahid_hrns = random.choice(ahid_hrns_list)
        payee_ahid_hrns = random.choice(ahid_hrns_list)
        currency_hrns = random.choice(currency_hrns_list)
        amount = random.randint(0, 100000)
        annotation = "test B" + str(n).zfill(4)
        if payer_ahid_hrns != payee_ahid_hrns:
            if display_random_selection:
                print(
                    currency_hrns + " : " \
                    + payer_ahid_hrns + " > " + payee_ahid_hrns \
                    + " | " + str(amount) \
                    + " | " + annotation
                )
            if test_payments:
                m = ah_payment(
                        payer_ahid_hrns,
                        payee_ahid_hrns,
                        currency_hrns,
                        amount,
                        annotation
                    )
                if m:
                    print(m)
    print("="*80)
