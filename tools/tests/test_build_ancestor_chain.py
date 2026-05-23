#!/home/slate/SLATE/venv/bin/python3

#from app.core.slate_core import register_identifier
#from app.core.slate_core import get_entity_types
#from app.core.slate_core import set_entity_type
#from app.core.slate_core import register_full_entity_set
#from app.core.slate_core import register_entity_type
#from app.core.slate_core import deregister_entity_type
#from app.core.slate_core import identify_entity
#from app.core.slate_core import new_primid
#from app.core.slate_core import new_account
#from app.core.slate_core import new_pairing
#from app.core.slate_core import new_namespace
#from app.core.slate_core import complete_parent_namespace
#from app.core.slate_core import is_ancestor
#from app.core.slate_core import _is_ancestor

from app.core.slate_core import build_ancestor_chain

#from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns



ns_fph_list, \
m = build_ancestor_chain("bb.cc", "bb.cc", ["qw", "er", "ty", "ui", "op"])
print(ns_fph_list)
