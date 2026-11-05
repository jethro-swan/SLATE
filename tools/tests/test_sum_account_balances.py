#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import sum_account_balances
from app.core.display import integer_to_money_format, integer_to_money_s_format


for owner_id in ["ah1.bb.cc", "ah2.bb.cc", "ah3.bb.cc"]:
    balance_sum, volume_sum, \
    m = sum_account_balances(owner_id, "money", "", "lt", "", False)
    print("\nahid = " + owner_id)
    categories = ["money", "htime", "utime", "energy", "unspecified"]
    for c in categories:
        print(
            c + ": (balance_sum, volume_sum) = (" \
            + integer_to_money_s_format(balance_sum[c]) + ", " \
            + integer_to_money_s_format(volume_sum[c]) + ")"
        )
