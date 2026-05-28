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



from app.core.exports import list_payments_in_currency
from app.core.exports import list_payments_for_account
from app.core.exports import dump_currency_payments_csv
from app.core.exports import dump_account_payments_csv
from app.core.exports import dump_currency_payments_table
from app.core.exports import dump_currency_payments
from app.core.exports import dump_currency_payments_html
from app.core.exports import dump_account_payments
from app.core.exports import dump_currency_payments

op_path = "/tmp/SLATE_test_exports/"

print("\n" + "-"*120)
print("Testing list_payments_in_currency( )")
payments_list, m = list_payments_in_currency("hrs.cc")
if m:
    print(m)
else:
    for payments_row in payments_list:
        print(payments_row)

#print("\n" + "-"*120)
#print("Testing list_payments_for_account( )")
#payments_list, m = list_payments_for_account(account_id)
#if m:
#    print(m)
#else:
#    for payments_row in payments_list:
#        print(payments_row)

print("\n" + "-"*120)
print("Testing dump_currency_payments_csv( )")
csv_filename, m = dump_currency_payments_csv("hrs.cc", True)
if m:
    print(m)
else:
    print("csv_filename = " + csv_filename)
    csv_filepath = "/home/slate/SLATE/app/export/" + csv_filename
    with open(csv_filepath, "r") as csvf:
        csv_contents = csvf.readlines()
    for csv_row in csv_contents:
        print(csv_row)

#print("\n" + "-"*120)
#print("Testing dump_account_payments_csv( )")
#csv_filename, m = dump_account_payments_csv(account_id, False)
#if m:
#    print(m)
#else:
#    print("csv_filename = " + csv_filename)
#    with open(csv_filename, "r") as csvf:
#        csv_contents = csvf.readlines()
#    for csv_row in csv_contents:
#        print(csv_row)

print("\n" + "-"*120)
print("Testing dump_dump_currency_payments_table( )")
out_path = op_path + "dump_currency_payments_table"
payments_table = dump_currency_payments_table("hrs.cc", out_path)
print(payments_table)

#print("\n" + "-"*120)
#print("Testing dump_currency_payments( )")
#payments_table = dump_currency_payments(currency_fph)
#print(payments_table)

print("\n" + "-"*120)
print("Testing dump_currency_payments_html( )")
out_path = op_path + "dump_currency_payments_table.html"
html_str = dump_currency_payments_html("hrs.cc", out_path)

#print("\n" + "-"*120)
#print("Testing dump_account_payments( )")
#all_payments, m = dump_account_payments(account_fph)
#print(all_payments)

print("\n" + "-"*120)
print("Testing dump_currency_payments( )")
all_payments, m = dump_currency_payments("hrs.cc")
print(all_payments)

print("\n" + "-"*120)
