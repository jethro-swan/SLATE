#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import pickle
import random

from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

from app.core.slate_core import new_namespace, new_currency, new_primid
from app.core.slate_core import split_hrns

from app.core.omtrad import *


#primid_fph, m = hrns_to_fph("bb.cc")

parent_fph, m = hrns_to_fph("cc")

primid_fph, \
primid_hrns, \
access_token, \
m = new_primid(
        "bb", parent_fph, "JW", "john@lrc.org.uk", "", "zxcvbnm", "123456"
    )
#primid_fph, m = hrns_to_fph("bb.cc")

nslist = ["uk.cc", "mon.uk.cc", "chep.mon.uk.cc"]
clist = ["kwh.cc", "hrs.cc", "kwh.uk.cc", "hrs.mon.uk.cc", "h.chep.mon.uk.cc"]





for ns in nslist:
    nsname, ns_parent_ns_hrns = split_hrns(ns)
    parent_namespace_fph, m = hrns_to_fph(ns_parent_ns_hrns)

    namespace_fph, \
    namespace_hrns, \
    m = new_namespace(
            nsname,
            parent_namespace_fph,
            "cc",
            primid_fph
        )

    print(namespace_fph + " > " + namespace_hrns)
    print()

for c in clist:
    cname, c_parent_ns_hrns = split_hrns(c)
    parent_namespace_fph, m = hrns_to_fph(c_parent_ns_hrns)

    currency_fph, \
    currency_hrns, \
    m = new_currency(
            cname,
            parent_namespace_fph,
            primid_fph,
            "",
            "",
            "cname"
        )

    print(currency_fph + " > " + currency_hrns)
    print()





#name1, namespace1 = split_hrns("tom.dick.harry")
#print(name1 + " : " + namespace1)

for ahid_hrns in ["ah1.bb.cc", "ah2.bb.cc", "ah3.bb.cc", "ah4.bb.cc"]:
#for ahid_hrns in ["ah5.bb.cc", "ah6.bb.cc", "ah7.bb.cc", "ah8.bb.cc"]:
    for c_hrns in ["cc", "hrs.cc", "kwh.cc"]:
    #for c_hrns in ["g£.cc", "MWh.cc", "g$.cc"]:
        p_fph = create_new_pairing("bb.cc", ahid_hrns, c_hrns)
        print(p_fph)


#ah1_fph = create_new_pairing("bb.cc", "ah1.cc", "cc")

#print(ah1_fph)

#print(fph_to_hrns(ah1_fph))

#with sqlite3.connect(ENTITIES_DB) as conn:
#    cursor = conn.cursor()
#    cursor.execute("SELECT pmap FROM primids;")
#    results = cursor.fetchall()
#    cursor.close()
#
#if results is None:
#    print("No pmaps found")
#else:
#    print(results)
#    for result in results[0]:
#        if result is None:
#            print("invalid pmap")
#        else:
#            pmap = pickle.loads(result)
#            print(pmap)


pmap, m = retrieve_pmap("bb.cc")

print("Retrieved pmap:")
print(pmap)
print()

complete_parent_namespace("zx.cv.l5.cald.mon.uk", primid_fph)
#currency_fph, currency_hrns, m = create_import_currency("qw.er.ty.ui.pa.uk")
#print(currency_fph)
#print(currency_hrns)
#print(m)

test_entity_identification = True
test_entity_identification = False

#run_payment_test_loop = False
run_payment_test_loop = True

#display_random_selection = False
display_random_selection = True

#test_payments = False
test_payments = True

ahid_hrns_list = ["ah1.bb.cc", "ah2.bb.cc", "ah3.bb.cc", "ah4.bb.cc"]
currency_hrns_list = ["cc", "hrs.cc", "kwh.cc"]

if test_entity_identification:
    for ahid_hrns in ahid_hrns_list:
        ahid_fph, \
        ahid_hrns, \
        etype, \
        m = identify_entity(ahid_hrns)
        if m:
            print(m)
        print(etype + ": " + ahid_fph + " > " + ahid_hrns)
    for currency_hrns in currency_hrns_list:
        currency_fph, \
        currency_hrns, \
        etype, \
        m = identify_entity(currency_hrns)
        if m:
            print(m)
        print(etype + ": " + currency_fph + " > " + currency_hrns)
    print()


if run_payment_test_loop:
    for n in range(100):
        payer_ahid_hrns = random.choice(ahid_hrns_list)
        payee_ahid_hrns = random.choice(ahid_hrns_list)
        currency_hrns = random.choice(currency_hrns_list)
        amount = random.randint(0, 100000)
        annotation = "test B" + str(n)
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
    print()
