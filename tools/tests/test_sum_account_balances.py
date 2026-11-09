#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import identify_entity
from app.core.slate_core import retrieve_pairing_account_fph
from app.core.slate_core import get_account_properties
from app.core.slate_core import sum_account_balances
from app.core.slate_core import sum_ahid_account_balances
from app.core.slate_core import sum_primid_account_balances
from app.core.display import integer_to_money_format, integer_to_money_s_format

ahid_accounts_balance_sum = {}
ahid_accounts_volume_sum = {}
for ahid_id in ["ah1.bb.cc", "ah2.bb.cc", "ah3.bb.cc", "ah4.bb.cc"]:
    ahid_fph, ahid_hrns, h_etypes, m = identify_entity(ahid_id)
    if m:
        print("m: " + m)
    else:
        balance_sum, volume_sum, \
        errors = sum_ahid_account_balances(ahid_fph, "", "lt", "")
        print("AHID: " + ahid_hrns)
        ahid_accounts_balance_sum[ahid_hrns] = balance_sum
        ahid_accounts_volume_sum[ahid_hrns] = volume_sum

        print("balance_sum = " + integer_to_money_s_format(balance_sum))
        print("volume_sum = " + integer_to_money_s_format(volume_sum))


    #
#    print("\nahid = " + ahid_hrns)
    #
#    ahid_accounts_sum[ahid_fph] = 0
    #
#    for currency_id in ["cc.cc", "h.hrs.cc", "hrs.cc", "kwh.cc"]:
#        currency_fph, currency_hrns, c_etypes, m = identify_entity(currency_id)
        #
#        account_fph, primid_fph, \
#        m = retrieve_pairing_account_fph(ahid_id, currency_id)
        #
#        currency_fph, owner_fph, balance, volume, active, \
#        account_type, account_category, account_units, \
#        account_metrical_equivalence, account_dimensions, \
#        m = get_account_properties(account_fph)
        #
#        print(
#            account_type + " | " \
#            + account_category + " | " \
#            + account_metrical_equivalence
#        )
        #
#        if (account_category == "money"):
#            print(balance)
#            ahid_accounts_sum[ahid_fph] += balance

#    balance_sum, volume_sum, \
#    m = sum_account_balances(ahid_fph, "money", "", "lt")
    #
#    print(balance_sum)
#    print("\nahid = " + ahid_hrns)
    #
#    print(
#        "balance_sum = " + integer_to_money_s_format(balance_sum["money"]) \
#        + " :: " \
#        + integer_to_money_s_format(ahid_accounts_sum[ahid_fph])
#    )

#    categories = ["money", "htime", "utime", "energy", "unspecified"]
#    for c in categories:
#        print(
#            c + ": (balance_sum, volume_sum) = (" \
#            + integer_to_money_s_format(balance_sum[c]) + ", " \
#            + integer_to_money_s_format(volume_sum[c]) + ")"
#        )
