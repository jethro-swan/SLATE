#!/home/slate/SLATE/venv/bin/python3

import sqlite3

from app.core.fph_hrns_maps import fph_to_hrns
from app.core.slate_core import list_currency_accounts
from app.core.slate_core import get_account_currency
from app.core.slate_core import get_account_properties
from app.core.slate_core import identify_entity
from app.core.slate_core import random_filename
from app.core.slate_core import list_ahids
from app.core.slate_core import list_accounts
from app.core.slate_core import sum_account_balances
from app.core.display import integer_to_money_format
from app.core.constants import GRAPHS


primid_id = "bb.cc"

ahids_fph_list = list_ahids(primid_id)

type = "money"

balance_sum = 0
volume_sum = 0

for ahid_fph in ahids_fph_list:
    ahid_hrns = fph_to_hrns(ahid_fph)
    print(ahid_hrns)
    print()
    accounts_fph_list, m = list_accounts(ahid_fph, "ahid")
    for account_fph in accounts_fph_list:
        currency_fph, owner_fph, balance, volume, active, \
        type, category, units, metrical_equivalence, dimensions, \
        m = get_account_properties(account_fph)
        currency_hrns = fph_to_hrns(currency_fph)
        print("    " + currency_hrns + " | " + ahid_hrns + " (", end="")
        print(account_fph + ")")
        if type is None:
            type = "none"
        if category is None:
            category = "none"
        if units is None:
            units = "none"
        if metrical_equivalence is None:
            metrical_equivalence = "none"
        if dimensions is None:
            dimensions = "none"
        print("    type: " + type)
        print("    category: " + category)
        print("    units: " + units)
        print("    metrical_equivalence: " + metrical_equivalence)
        print("    dimensions: " + dimensions)
        print("    balance:         " + integer_to_money_format(balance))
        balance_sum += balance
        print("    summed balance = " + integer_to_money_format(balance_sum))
        print()
print()





def list_currency_payments(currency_id):

    currency_fph, currency_hrns, etype, m = identify_entity(currency_id)
    if not currency_fph:
        return []
    if not ("currency" in etypes):
        return []

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified *currency*:
        cursor.execute(
            "SELECT timestamp, payment_id, " \
            + "payer_fph, payee_fph, currency_fph, amount, " \
            + "payer_balance, payee_balance, annotation " \
            + "FROM payments WHERE currency_fph = ? ", (currency_fph,)
        )
        all_payments = cursor.fetchall()
        cursor.close()
    if all_payments is None:
        return []





def test_sum_account_balances(
        owner_id,
        account_category,
        account_units,
        account_metrical_equivalence,
        account_dimensions
    ):

    owner_fph, owner_hrns, etype, m = identify_entity(owner_id)
    if not owner_fph:
        return owner_id + " is not a registered identifier"
    if not ("primid" in etypes):
        return owner_hrns + " has no registered primid"

    balance_sum, volume_sum, \
    m = sum_account_balances(
            owner_fph,
            account_category,
            account_units,
            account_metrical_equivalence,
            account_dimensions
        )
