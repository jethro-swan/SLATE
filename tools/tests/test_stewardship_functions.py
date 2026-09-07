#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import fph_to_hrns
from app.core.slate_core import identify_entity

from app.core.stewardship import add_or_remove_steward
from app.core.stewardship import add_or_remove_stewardship
from app.core.stewardship import add_namespace_steward
from app.core.stewardship import add_currency_steward
from app.core.stewardship import remove_namespace_steward
from app.core.stewardship import remove_currency_steward
from app.core.stewardship import list_stewards
from app.core.stewardship import list_namespace_stewardships
from app.core.stewardship import list_currency_stewardships
from app.core.stewardship import set_currency_parameter

def show_namespace_stewards(namespace_id):
    stewards_fph_list, m = list_stewards(namespace_id, "namespace")
    if m:
        print(m)
        return
    stewards_hrns_list = []
    for steward_fph in stewards_fph_list:
        stewards_hrns_list.append(fph_to_hrns(steward_fph))
    print("namespace stewards of " + namespace_id + " are : ", end="")
    print(stewards_hrns_list)

def show_namespace_stewardships(steward_id):
    stewardships_fph_list, m = list_namespace_stewardships(steward_id)
    if m:
        print(m)
        return
    stewardships_hrns_list = []
    for stewardship_fph in stewardships_fph_list:
        stewardships_hrns_list.append(fph_to_hrns(stewardship_fph))
    print("namespace stewardships of " + steward_id + " are: ", end="")
    print(stewardships_hrns_list)

def show_currency_stewards(currency_id):
    stewards_fph_list, m = list_stewards(currency_id, "currency")
    if m:
        print(m)
        return
    stewards_hrns_list = []
    for steward_fph in stewards_fph_list:
        stewards_hrns_list.append(fph_to_hrns(steward_fph))
    print("currency stewards of " + currency_id + " are: ", end="")
    print(stewards_hrns_list)

def show_currency_stewardships(steward_id):
    stewardships_fph_list, m = list_currency_stewardships(steward_id)
    if m:
        print(m)
        return
    stewardships_hrns_list = []
    for stewardhip_fph in stewardships_fph_list:
        stewardships_hrns_list.append(fph_to_hrns(stewardhip_fph))
    print("currency stewardships of " + steward_id + ": ", end="")
    print(stewardships_hrns_list)


print("-"*120)
show_namespace_stewards("bb.cc")
show_namespace_stewards("dd.cc")
show_namespace_stewards("ee.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")
print("-"*120)
show_currency_stewards("bb.cc")
show_currency_stewards("dd.cc")
show_currency_stewards("ee.cc")
show_currency_stewardships("bb.cc")
show_currency_stewardships("dd.cc")
show_currency_stewardships("ee.cc")
print("-"*120)

#m = add_or_remove_steward("bb.cc", "namespace", "add", "bb.cc", "bb.cc")
add_namespace_steward("bb.cc", "bb.cc", "bb.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
print()
#m = add_or_remove_steward("bb.cc", "namespace", "add", "bb.cc", "dd.cc")
#m = add_or_remove_stewardship("bb.cc", "namespace", "add", "dd.cc", "dd.cc")
add_namespace_steward("bb.cc", "bb.cc", "dd.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("dd.cc")
print()
#m = add_or_remove_steward("bb.cc", "namespace", "add", "bb.cc", "ee.cc")
add_namespace_steward("bb.cc", "bb.cc", "ee.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("ee.cc")
print()
remove_namespace_steward("bb.cc", "bb.cc", "bb.cc")
show_namespace_stewards("bb.cc")
print()
remove_namespace_steward("bb.cc", "bb.cc", "dd.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("dd.cc")
print()
remove_namespace_steward("bb.cc", "bb.cc", "ee.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("ee.cc")
print()

#m = add_or_remove_steward("bb.cc", "namespace", "add", "bb.cc", "bb.cc")
add_currency_steward("bb.cc", "bb.cc", "bb.cc")
show_currency_stewards("bb.cc")
show_currency_stewardships("bb.cc")
print()
#m = add_or_remove_steward("bb.cc", "namespace", "add", "bb.cc", "dd.cc")
#m = add_or_remove_stewardship("bb.cc", "namespace", "add", "dd.cc", "dd.cc")
add_currency_steward("bb.cc", "bb.cc", "dd.cc")
show_currency_stewards("bb.cc")
show_currency_stewardships("dd.cc")
print()
#m = add_or_remove_steward("bb.cc", "namespace", "add", "bb.cc", "ee.cc")
add_currency_steward("bb.cc", "bb.cc", "ee.cc")
show_currency_stewards("bb.cc")
show_currency_stewardships("ee.cc")
print()
remove_currency_steward("bb.cc", "bb.cc", "bb.cc")
show_currency_stewards("bb.cc")
show_currency_stewardships("bb.cc")
print()
remove_currency_steward("bb.cc", "bb.cc", "dd.cc")
show_currency_stewards("bb.cc")
show_currency_stewardships("dd.cc")
print()
remove_currency_steward("bb.cc", "bb.cc", "ee.cc")
show_currency_stewards("bb.cc")
show_currency_stewardships("ee.cc")
print()
