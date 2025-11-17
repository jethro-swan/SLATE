#!/home/slate/SLATE/venv/bin/python3

from app.core.fph_hrns_maps import fph_to_hrns
from app.core.slate_core import identify_entity
from app.core.slate_core import get_currency_properties
from app.core.slate_core import activate_currency, deactivate_currency
from app.core.slate_core import activate_namespace, deactivate_namespace
from app.core.slate_core import open_namespace, close_namespace
from app.core.slate_core import open_currency, close_currency
from app.core.slate_core import add_namespace_steward, remove_namespace_steward
from app.core.slate_core import add_currency_steward, remove_currency_steward
from app.core.slate_core import get_namespace_properties
from app.core.display import truefalse


currency_hrns = "kwh.cc"
namespace_hrns = "cc"

steward_hrns = "cc"

for i in range(3):

    m = activate_namespace(namespace_hrns, steward_hrns)
    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(namespace_hrns)
    print(namespace_hrns + " :: active = " + truefalse(active))
    print(namespace_hrns + " :: open = " + truefalse(open))

    m = deactivate_namespace(namespace_hrns, steward_hrns)
    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(namespace_hrns)
    print(namespace_hrns + " :: active = " + truefalse(active))
    print(namespace_hrns + " :: open = " + truefalse(open))

    m = open_namespace(namespace_hrns, steward_hrns)
    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(namespace_hrns)
    print(namespace_hrns + " :: active = " + truefalse(active))
    print(namespace_hrns + " :: open = " + truefalse(open))

    m = close_namespace(namespace_hrns, steward_hrns)
    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(namespace_hrns)
    print(namespace_hrns + " :: active = " + truefalse(active))
    print(namespace_hrns + " :: open = " + truefalse(open))

    add_namespace_steward(namespace_hrns, steward_hrns, "dd.cc")
    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(namespace_hrns)
    for steward_fph in stewards_list:
        print("steward: " + fph_to_hrns(steward_fph))

    add_namespace_steward(namespace_hrns, steward_hrns, "bb.cc")
    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(namespace_hrns)
    for steward_fph in stewards_list:
        print("steward: " + fph_to_hrns(steward_fph))

    remove_namespace_steward(namespace_hrns, steward_hrns, "dd.cc")
    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(namespace_hrns)
    for steward_fph in stewards_list:
        print("steward: " + fph_to_hrns(steward_fph))

    remove_namespace_steward(namespace_hrns, steward_hrns, "bb.cc")
    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(namespace_hrns)
    for steward_fph in stewards_list:
        print("steward: " + fph_to_hrns(steward_fph))

    print("---")

add_namespace_steward(namespace_hrns, steward_hrns, "dd.cc")
add_namespace_steward(namespace_hrns, steward_hrns, "bb.cc")
add_namespace_steward(namespace_hrns, steward_hrns, "cc.cc")
active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
m = get_namespace_properties(namespace_hrns)
for steward_fph in stewards_list:
    print("steward: " + fph_to_hrns(steward_fph))


print("-"*80)

for i in range(3):

    m = activate_currency(currency_hrns, steward_hrns)
    currency_fph, currency_hrns, active, open, private, sandbox, \
    currency_type, currency_category, currency_units, \
    currency_metrical_equivalence, currency_dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_hrns)
    print(currency_hrns + " :: active = " + truefalse(active))
    print(currency_hrns + " :: open = " + truefalse(open))

    m = deactivate_currency(currency_hrns, steward_hrns)
    currency_fph, currency_hrns, active, open, private, sandbox, \
    currency_type, currency_category, currency_units, \
    currency_metrical_equivalence, currency_dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_hrns)
    print(currency_hrns + " :: active = " + truefalse(active))
    print(currency_hrns + " :: open = " + truefalse(open))

    m = open_currency(currency_hrns, steward_hrns)
    currency_fph, currency_hrns, active, open, private, sandbox, \
    currency_type, currency_category, currency_units, \
    currency_metrical_equivalence, currency_dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_hrns)
    print(currency_hrns + " :: active = " + truefalse(active))
    print(currency_hrns + " :: open = " + truefalse(open))

    close_currency(currency_hrns, steward_hrns)
    currency_fph, currency_hrns, active, open, private, sandbox, \
    currency_type, currency_category, currency_units, \
    currency_metrical_equivalence, currency_dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_hrns)
    print(currency_hrns + " :: active = " + truefalse(active))
    print(currency_hrns + " :: open = " + truefalse(open))

    add_currency_steward(currency_hrns, steward_hrns, "dd.cc")
    currency_fph, currency_hrns, active, open, private, sandbox, \
    currency_type, currency_category, currency_units, \
    currency_metrical_equivalence, currency_dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_hrns)
    for steward_fph in stewards_list:
        print("steward: " + fph_to_hrns(steward_fph))

    add_currency_steward(currency_hrns, steward_hrns, "bb.cc")
    currency_fph, currency_hrns, active, open, private, sandbox, \
    currency_type, currency_category, currency_units, \
    currency_metrical_equivalence, currency_dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_hrns)
    for steward_fph in stewards_list:
        print("steward: " + fph_to_hrns(steward_fph))

    remove_currency_steward(currency_hrns, steward_hrns, "dd.cc")
    currency_fph, currency_hrns, active, open, private, sandbox, \
    currency_type, currency_category, currency_units, \
    currency_metrical_equivalence, currency_dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_hrns)
    for steward_fph in stewards_list:
        print("steward: " + fph_to_hrns(steward_fph))

    remove_currency_steward(currency_hrns, steward_hrns, "bb.cc")
    currency_fph, currency_hrns, active, open, private, sandbox, \
    currency_type, currency_category, currency_units, \
    currency_metrical_equivalence, currency_dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_hrns)
    for steward_fph in stewards_list:
        print("steward: " + fph_to_hrns(steward_fph))

    print("---")

add_currency_steward(currency_hrns, steward_hrns, "jw.cc")
add_currency_steward(currency_hrns, steward_hrns, "bb.cc")
add_currency_steward(currency_hrns, steward_hrns, "dd.cc")
currency_fph, currency_hrns, active, open, private, sandbox, \
currency_type, currency_category, currency_units, \
currency_metrical_equivalence, currency_dimensions, \
prefix, suffix, default_account_name, stewards_list, \
m = get_currency_properties(currency_hrns)
for steward_fph in stewards_list:
    print("steward: " + fph_to_hrns(steward_fph))
