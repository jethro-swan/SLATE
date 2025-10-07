#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import register_identifier
from app.core.slate_core import get_entity_types
from app.core.slate_core import set_entity_type
from app.core.slate_core import register_full_entity_set
from app.core.slate_core import register_entity_type
from app.core.slate_core import deregister_entity_type
from app.core.slate_core import identify_entity
from app.core.slate_core import new_primid
from app.core.slate_core import new_account
from app.core.slate_core import new_pairing
from app.core.slate_core import new_namespace
from app.core.slate_core import complete_parent_namespace
from app.core.slate_core import is_ancestor
from app.core.slate_core import _is_ancestor

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns

def list_etypes(e_fph):
    etypes, m = get_entity_types(e_fph)
    print("etypes: ", end="")
    print(etypes)

qq_fph = register_identifier("qq.cc")
print("qq.cc")
print(qq_fph + " > " + fph_to_hrns(qq_fph))
qq_fph2, m = hrns_to_fph("qq.cc")
if qq_fph2 != qq_fph:
    print("Map inversion failure")

list_etypes(qq_fph)

register_entity_type(qq_fph, "currency")

list_etypes(qq_fph)

register_entity_type(qq_fph, "namespace")

list_etypes(qq_fph)

register_entity_type(qq_fph, "ahid")

list_etypes(qq_fph)

deregister_entity_type(qq_fph, "currency")

list_etypes(qq_fph)

deregister_entity_type(qq_fph, "ahid")

list_etypes(qq_fph)

deregister_entity_type(qq_fph, "namespace")

list_etypes(qq_fph)

register_entity_type(qq_fph, "currency")

list_etypes(qq_fph)

register_entity_type(qq_fph, "namespace")

list_etypes(qq_fph)

register_entity_type(qq_fph, "ahid")

list_etypes(qq_fph)

deregister_entity_type(qq_fph, "currency")
deregister_entity_type(qq_fph, "namespace")
deregister_entity_type(qq_fph, "ahid")

list_etypes(qq_fph)

register_full_entity_set(qq_fph)
list_etypes(qq_fph)

print("\nCreating test primid\n")

cthulhu_fph, cthulhu_hrns, access_token, \
m = new_primid(
        "cthulhu",
        "cc",
        "Cthulhu",
        "cthulhu@rlyeh.net",
        "",
        "yog-sothoth",
        "987654",
        "kwh.cc"
    )

print("primid_fph: " + cthulhu_fph)
print("primid_hrns: " + cthulhu_hrns)
print("access_token: " + access_token)
print("primid creation message:")
print(m)

cthulhu_fph, cthulhu_hrns, etypes, m = identify_entity(cthulhu_fph)
print("cthulhu_fph = " + cthulhu_fph)
print("cthulhu_hrns = " + cthulhu_hrns)
print("etypes = ", end="")
print(etypes)
if m:
    print(m)

print("\nCreating test account ...\n")

account_fph, account_hrns, \
m = new_account(
        "montecristo",
        "bb.cc",
        "bb.cc",
        "hrs.cc"
    )
print("test account: " + account_fph + " > " + account_hrns)

print("\nCreating test pairing ...\n")

account_fph, account_hrns, \
m = new_pairing(
        cthulhu_hrns,     # *primid* HRNS or FPH
        "ah1.cthulhu.cc", # HRNS (may not exist already)
        "hrs.cc"          # HRNS or FPH (must exist already)
    )

print("account_fph = " + account_fph)
print("account_hrns = " + account_hrns)

ns = []
ns_hrns = "bb.cc"
for n in ["zz", "yy", "xx", "ww", "vv", "uu"]:
    ns_fph, ns_hrns, m = new_namespace(n, ns_hrns, "cc", "bb.cc")
    ns.append(ns_hrns)
for i in range(len(ns)):
    print(ns[i])
print(bool(is_ancestor(ns[4], ns[0])))
print(bool(_is_ancestor(ns[4], ns[0])))
