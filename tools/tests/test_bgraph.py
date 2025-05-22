#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import list_currency_accounts
from app.core.slate_core import get_account_currency
from app.core.slate_core import get_account_specific_properties
from app.core.slate_core import identify_entity


test_currency = "kwh.cc"

account_fph_list = list_currency_accounts(test_currency)

account = {}
sum = 0

for account_fph in account_fph_list:

    currency_fph, \
    owner_fph, \
    ahid_fph, \
    balance, \
    volume, \
    m = get_account_specific_properties(account_fph)

    account_fph, \
    account_hrns, \
    etype, \
    m = identify_entity(account_fph)

    account[account_fph] = balance

    sum += balance

print(account)

for account_fph in account.keys():
    print(account[account_fph])
    print(account_fph + " : " + str(account[account_fph]))

print()
print(str(sum))
