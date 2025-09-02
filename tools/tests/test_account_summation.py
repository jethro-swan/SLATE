#!/home/slate/SLATE/venv/bin/python3

#import sqlite3
#from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
#from app.core.constants import ENTITIES_DB
from app.core.slate_core import sum_account_balances
from app.core.slate_core import integer_to_money_format

owner_id = "ah1.bb.cc"

balance_sum, volume_sum, \
m = sum_account_balances(
        owner_id,
        "unspecified",
        "",
        "",
        ""
    )

if m:
    print(m)

#print("balance_sum: " + integer_to_money_format(balance_sum))
#print("volume_sum:  " + integer_to_money_format(volume_sum))

for k in balance_sum.keys():
    print(k + ":balance_sum \t" + integer_to_money_format(balance_sum[k]))
    print(k + ":volume_sum \t" + integer_to_money_format(volume_sum[k]))




volume_sum
