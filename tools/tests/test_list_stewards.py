#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import identify_entity
from app.core.slate_core import list_stewards

entity_id = "bb.cc"
entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)


stewards, m = list_stewards(entity_id, "currency")
if m:
    print(m)
print("currency stewards:", end="")
print(stewards)
