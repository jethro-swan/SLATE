#!/home/slate/SLATE/venv/bin/python3


from app.core.slate_core import list_currency_accounts
from app.core.slate_core import get_account_specific_properties



accounts = list_currency_accounts("cc")

balances = []

for account_fph in accounts:

    currency_fph, \
    owner_fph, \
    ahid_fph, \
    balance, \
    volume, \
    m = get_account_specific_properties(account_fph)

    balances.append(balance)

    print(balance)
