#!/home/john/NESTS/SLATE/venv/bin/python3

import sys, os
import random
import string


from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.common import filename_timestamp as timestamp
from app.core.slate_core import account_status
from app.core.payments import payment
from app.core.common import filename_timestamp
from app.core.display import integer_to_money_s_format

with open("accounts_created", "r") as f:
    accounts_list = f.readlines()

#
l_accounts = []
for a in accounts_list:
    account_fph = a.strip()
    l_accounts.append(account_fph)

for account_fph in l_accounts:
    exists, \
    active, \
    currency_fph, \
    owner_fph, \
    balance, \
    m = account_status(account_fph)
#    print(account_fph + " > " + fph_to_hrns(account_fph))
#    print(
#        account_fph + " > " + fph_to_hrns(account_fph) + "\t" \
#        + " (currency: " + fph_to_hrns(currency_fph) + ")\t" \
#        + " (owner: " + fph_to_hrns(owner_fph) + ")"
#    )


with open("payments_made", "a") as f:
    for p in range(500):
        payer_account_fph = random.choice(l_accounts)
        payer_account_exists, \
        payer_account_active, \
        payer_account_currency_fph, \
        payer_account_owner_fph, \
        payer_account_balance, \
        m = account_status(payer_account_fph)
        #
        payee_account_currency_fph = ""
        payee_account_fph = ""
        while (payer_account_currency_fph != payee_account_currency_fph) \
              or (payer_account_fph == payee_account_fph):
            payee_account_fph = random.choice(l_accounts)
            payee_account_exists, \
            payee_account_active, \
            payee_account_currency_fph, \
            payee_account_owner_fph, \
            payee_account_balance, \
            m = account_status(payee_account_fph)

        amount = random.randint(10, 10000)
        print(amount)

        annotation = "Paid " + integer_to_money_s_format(amount) + " from " \
                   + fph_to_hrns(payer_account_owner_fph) + " to " \
                   + fph_to_hrns(payee_account_owner_fph)

        m = payment(payer_account_fph, payee_account_fph, amount, annotation)
