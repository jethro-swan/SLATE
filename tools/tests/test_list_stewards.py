#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import identify_entity
from app.core.slate_core import list_stewards
from app.core.slate_core import add_namespace_stewardship
from app.core.slate_core import add_currency_stewardship
from app.core.slate_core import remove_currency_stewardship
from app.core.slate_core import modify_currency_stewardship
from app.core.slate_core import add_or_remove_steward
from app.core.slate_core import remove_namespace_steward
from app.core.slate_core import set_currency_parameter





entity_id = "bb.cc"
entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)


stewards, m = list_stewards(entity_id, "currency")
if m:
    print(m)
print("currency stewards:", end="")
print(stewards)
