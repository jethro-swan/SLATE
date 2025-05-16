#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import pickle

from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

from app.core.slate_core import new_namespace, new_currency, new_primid
from app.core.slate_core import split_hrns

from app.core.om_trad import *


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

complete_parent_namespace_chain("zx.cv.l5.cald.mon.uk")
#currency_fph, currency_hrns, m = create_import_currency("qw.er.ty.ui.pa.uk")
#print(currency_fph)
#print(currency_hrns)
#print(m)
