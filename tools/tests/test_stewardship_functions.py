#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import fph_to_hrns
from app.core.slate_core import identify_entity
from app.core.slate_core import list_stewards
from app.core.slate_core import add_or_remove_steward
from app.core.slate_core import add_namespace_steward
from app.core.slate_core import add_currency_steward
from app.core.slate_core import remove_namespace_steward
from app.core.slate_core import remove_currency_steward
from app.core.slate_core import list_namespace_stewardships
from app.core.slate_core import list_currency_stewardships
from app.core.slate_core import set_currency_parameter



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
show_namespace_stewardships("bb.cc")
show_currency_stewards("bb.cc")
show_currency_stewardships("bb.cc")
print("-"*120)

show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")

m = add_or_remove_steward("bb.cc", "namespace", "add", "bb.cc", "dd.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")
m = add_or_remove_steward("bb.cc", "namespace", "add", "bb.cc", "ee.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")
m = add_or_remove_steward("bb.cc", "namespace", "remove", "bb.cc", "dd.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")
m = add_or_remove_steward("bb.cc", "namespace", "remove", "bb.cc", "ee.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")
print("-"*120)
show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")
print("\nadd_namespace_steward ...")
m = add_namespace_steward("bb.cc", "bb.cc", "dd.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")
m = add_namespace_steward("bb.cc", "bb.cc", "ee.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")
print("\nremove_namespace_steward ...")
m = remove_namespace_steward("bb.cc", "bb.cc", "dd.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")
m = remove_namespace_steward("bb.cc", "bb.cc", "ee.cc")
show_namespace_stewards("bb.cc")
show_namespace_stewardships("bb.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("ee.cc")
print("-"*120)







print("\nadd_currency_steward ...")
m = add_currency_steward("bb.cc", "bb.cc", "dd.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("dd.cc")
stewards, m = list_stewards("bb.cc", "currency")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("dd.cc")

print("\nremove_currency_steward ...")
m = remove_currency_steward("bb.cc", "bb.cc", "dd.cc")
show_namespace_stewardships("dd.cc")
show_namespace_stewardships("dd.cc")


add_namespace_steward("dd.cc", "dd.cc", "bb.cc")
