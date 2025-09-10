#!/home/slate/SLATE/venv/bin/python3

from app.core.constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from app.core.fph_hrns_maps import record_private_namespace_root
from app.core.fph_hrns_maps import get_private_namespace_root
from app.core.slate_core import create_entities_db
from app.core.dbm_functions import dbm_list_entries, dbm_keys
import random


print("\nList full FPF set used as keys and values\n")

fph_list = dbm_keys(FPH_TO_HRNS_MAP)
for fph in fph_list:
    print(fph)



#print("\nList sample FPF set used as keys and values\n")
print("\nList key:value mappings saved\n")
klist = []
#print(fph_list)
for i in range(10):
#    print(i)
    k = random.choice(fph_list)
#    print("k = " + k + ", ", end="")
    v = random.choice(fph_list)
#    print("v = " + v + " : ", end="")
    klist.append(k)
#    klist.remove(k)
    fph_list.remove(k)
    if record_private_namespace_root(k, v):
        print(k + " > " + v + "     mapping saved")
    else:
        print("Unable to save mapping")

print()
print("\nList key:value mappings retrieved\n")
for k in klist:
    v = get_private_namespace_root(k)
    print(k + " > " + v + "     mapping retrieved")

print("\nList key:value mappings overwritten\n")

for k in klist:
    v = random.choice(fph_list)
    if record_private_namespace_root(k, v):
        print(k + " > " + v + "     mapping saved")
    else:
        print("Unable to save mapping")

print("\nOverwritten key:value mappings retrieved\n")
for k in klist:
    v = get_private_namespace_root(k)
    print(k + " > " + v + "     mapping retrieved")
print()


create_entities_db("a71762cc9f7ec34dfee8b855e9f15bc6")
