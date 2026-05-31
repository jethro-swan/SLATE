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



from app.core.exports import list_currency_payments
from app.core.exports import list_account_payments
from app.core.exports import dump_currency_payments_csv
from app.core.exports import dump_account_payments_csv
from app.core.exports import dump_currency_payments_table
from app.core.exports import dump_currency_payments
from app.core.exports import dump_currency_payments_html
from app.core.exports import dump_account_payments
from app.core.exports import dump_currency_payments

op_path = "/tmp/SLATE_test_exports/"
#test_account_fph = "05015e6c4c8cb18c3fff3a18071590b7"
test_account_fph = "0c94e22da2add5b48acf5b3dfd3c2edb"
export_path = "/home/slate/SLATE/app/export/"

def test_list_currency_payments():
    print("\n"*5 + "-"*120)
    print("Testing list_currency_payments( )\n")
    payments_list, m = list_currency_payments("hrs.cc")
    if m:
        print(m)
    else:
        for payments_row in payments_list:
            print(payments_row)

def test_list_account_payments():
    print("\n"*4 + "-"*120)
    print("Testing list_account_payments( )\n")
    payments_list, m = list_account_payments(test_account_fph)
    if m:
        print(m)
    else:
        for payments_row in payments_list:
            print(payments_row)

def test_dump_currency_payments_csv():
    print("\n"*4 + "-"*120)
    print("Testing dump_currency_payments_csv( )\n")
    csv_filename, m = dump_currency_payments_csv("hrs.cc", True)
    if m:
        print(m)
    else:
        print("csv_filename = " + csv_filename + "\n")
        csv_filepath = "/home/slate/SLATE/app/export/" + csv_filename
        with open(csv_filepath, "r") as csvf:
            csv_contents = csvf.readlines()
        for csv_row in csv_contents:
            print(csv_row.strip())

def test_dump_account_payments_csv():
    print("\n"*4 + "-"*120)
    print("Testing dump_account_payments_csv( )\n")
    csv_filename, m = dump_account_payments_csv(test_account_fph, False)
    csv_filepath = export_path + csv_filename
    if m:
        print(m)
    else:
        print("csv_filename = " + csv_filename + "\n")
        with open(csv_filepath, "r") as csvf:
            csv_contents = csvf.readlines()
        for csv_row in csv_contents:
            print(csv_row.strip())

def test_dump_currency_payments_html():
    print("\n"*4 + "-"*120)
    print("Testing dump_currency_payments_html( )\n")
    out_path = op_path + "dump_currency_payments_table.html"
    html_str = dump_currency_payments_html("hrs.cc", out_path)

    #print("\n" + "-"*120)
    #print("Testing dump_account_payments( )")
    #all_payments, m = dump_account_payments(account_fph)
    #print(all_payments)

def test_dump_currency_payments():
    print("\n"*4 + "-"*120)
    print("Testing dump_currency_payments( )\n")
    all_payments = dump_currency_payments("hrs.cc")
    print(all_payments)

def test_dump_currency_payments_table():
    print("\n"*4 + "-"*120)
    print("Testing dump_currency_payments_table( )\n")
    out_path = op_path + "dump_currency_payments_table"
    payments_table = dump_currency_payments_table("hrs.cc")
    print(payments_table)

    #print("\n" + "-"*120)
    #print("Testing dump_currency_payments( )")
    #payments_table = dump_currency_payments(currency_fph)
    #print(payments_table)


#test_list_currency_payments()
test_list_account_payments()
#test_dump_currency_payments_csv()
test_dump_account_payments_csv()
#test_dump_currency_payments()
#test_dump_currency_payments_table()
#test_dump_currency_payments_html()


print("\n" + "-"*120)
