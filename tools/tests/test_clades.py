#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import list_ancestors_fph
from app.core.slate_core import most_recent_clade
from app.core.slate_core import most_recent_concestor
from app.core.slate_core import get_list_concestor
from app.core.slate_core import hrns_strip_concestor
from app.core.slate_core import prune_payment_pair_hrns
from app.core.slate_core import fph_to_hrns

test_hrns_1 = "cc"
test_hrns_2 = "bb.cc"
test_hrns_3 = "uu.vv.ww.xx.yy.zz.bb.cc"
test_hrns_4 = "xx.yy.zz.bb.cc"
test_hrns_5 = "vv.ww.xx.yy.zz.bb.cc"
test_hrns_6 = "ww.xx.yy.zz.bb.cc"

test_hrns_list = [
#    test_hrns_1,
#    test_hrns_2,
    test_hrns_3,
    test_hrns_4,
    test_hrns_5,
    test_hrns_6
]


ancestors, clades, m = list_ancestors_fph(test_hrns_1)
if m:
    print(m)
print("test ancestors FPH = ", end="")
print(ancestors)
print("test clades FPH = ", end="")
print(clades)
print()
print("test ancestors HRNS:")
for fph in ancestors:
    print(fph_to_hrns(fph))
print()
print("test clades HRNS:")
for fph in clades:
    print(fph_to_hrns(fph))
print()
nearest_clade, m = most_recent_clade(test_hrns_1)
print("most recent clade: " + nearest_clade)

print()

id1, id2, concestor, m = most_recent_concestor(test_hrns_3, test_hrns_4)
print("truncated id1: ", end="")
print(id1)
print("truncated id2: ", end="")
print(id2)
print("concestor: ", end="")
print(concestor)

print()
print("test_hrns_list = ", end="")
print(test_hrns_list)
concestor_hrns = get_list_concestor(test_hrns_list)
print("concestor: ", end="")
print(concestor_hrns)

print()
print("Testing hrns_strip_concestor( )")
for entity_hrns in test_hrns_list:
    entity_hrns_local, m = hrns_strip_concestor(entity_hrns, concestor_hrns)
    if m:
        print(m)
    else:
        print("entity_hrns_local = " + entity_hrns_local)

print()
print("prune_payment_pair_hrns( )")
for l in range(1, len(test_hrns_list)):
    hrns1 = test_hrns_list[l-1]
    hrns2 = test_hrns_list[l]
    print(hrns1 + " | " + hrns2 + " >>> ", end="")
    currency_hrns_short, payer_ahid_hrns_short, concestor_hrns, \
    m = prune_payment_pair_hrns(hrns1, hrns2)
    if m:
        print(m)
    print(
        currency_hrns_short + " | " \
        + payer_ahid_hrns_short + " | " \
        + concestor_hrns
    )
