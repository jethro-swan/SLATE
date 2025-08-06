#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import register_identifier
from app.core.slate_core import get_entity_types
from app.core.slate_core import set_entity_type
from app.core.slate_core import register_full_entity_set
from app.core.slate_core import register_entity_type
from app.core.slate_core import deregister_entity_type
#from app.core.slate_core import
#from app.core.slate_core import
#from app.core.slate_core import
#from app.core.slate_core import
from app.core.slate_core import new_primid
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
#set_entity_type(qq_fph, "namespace", True)

list_etypes(qq_fph)

register_entity_type(qq_fph, "namespace")
#set_entity_type(qq_fph, "currency", True)

list_etypes(qq_fph)

register_entity_type(qq_fph, "ahid")
#set_entity_type(qq_fph, "ahid", True)

list_etypes(qq_fph)

deregister_entity_type(qq_fph, "currency")

list_etypes(qq_fph)

deregister_entity_type(qq_fph, "ahid")

list_etypes(qq_fph)

deregister_entity_type(qq_fph, "namespace")

list_etypes(qq_fph)

register_entity_type(qq_fph, "currency")
#set_entity_type(qq_fph, "namespace", True)

list_etypes(qq_fph)

register_entity_type(qq_fph, "namespace")
#set_entity_type(qq_fph, "currency", True)

list_etypes(qq_fph)

register_entity_type(qq_fph, "ahid")
#set_entity_type(qq_fph, "ahid", True)

list_etypes(qq_fph)

deregister_entity_type(qq_fph, "currency")
deregister_entity_type(qq_fph, "namespace")
deregister_entity_type(qq_fph, "ahid")

list_etypes(qq_fph)

register_full_entity_set(qq_fph)
list_etypes(qq_fph)



primid_fph, \
primid_hrns, \
access_token, \
m = new_primid(
        "cthulhu",
        "cc",
        "Cthulhu",
        "cthulhu@rlyeh.net",
        "",
        "yog-sothoth",
        "987654"
    )

print("primid_fph: " + primid_fph)
print("primid_hrns: " + primid_hrns)
print("access_token: " + access_token)
print("primid creation message:")
print(m)
