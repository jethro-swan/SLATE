#!/home/slate/SLATE/venv/bin/python3

import random, string



from app.core.slate_core import create_currencies_from_list
from app.core.slate_core import create_pairings_from_list

parent_id = "bb.cc"


currency_list = []

for i in range(20):
    n = []
    for _ in range(random.randint(5, 8)):
        n.append(random.choice(string.ascii_letters.lower()))
    name = ''.join(n)
    print("name = " + name)
    currency = {}
    # currency_name = currency["name"]
    currency["name"] = name
    currency["parent"] = parent_id
    currency["steward"] = "bb.cc"
    currency["prefix"] = ""
    currency["suffix"] = ""
    currency["default_account_name"] = name
    currency["account_type"] = "scalar"
    currency["category"] = "money"
    currency["units"] = ""
    currency["metrical_equivalence"] = ""
    currency["dimensions"] = ""
    currency_list.append(currency)

print("\ncurrency_list:")
print(currency_list)
print()


currency_list, \
errors = create_currencies_from_list("bb.cc", currency_list)

print("errors: " + errors)

print("currency_list:")
print(currency_list)
print()

errors, \
invalid_currencies = create_pairings_from_list("bb.cc", "bb.cc", currency_list)

print("errors: " + errors)
