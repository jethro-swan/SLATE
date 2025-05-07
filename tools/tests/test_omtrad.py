#!/home/john/NESTS/SLATE/venv/bin/python3

import sqlite3
import pickle

from app.core.om_trad import *




#name1, namespace1 = split_hrns("tom.dick.harry")
#print(name1 + " : " + namespace1)


ah1_fph = create_new_pairing("bb.cc", "ah15.cc", "cc")

print(ah1_fph)

print(fph_to_hrns(ah1_fph))

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


pmap , m = retrieve_pmap("bb.cc")

print(pmap)
