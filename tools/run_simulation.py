#!/home/john/NESTS/SLATE/venv/bin/python3

import sys
import os
import random
import string
import random
import argparse

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.common import filename_timestamp as timestamp
from app.core.slate_core import account_status
from app.core.payments import payment
from app.core.common import filename_timestamp
from app.core.display import integer_to_money_s_format



#-------------------------------------------------------------------------------
# Default values:

default_input_filename = "accounts_created"
default_output_filename = "payments_made"
default_minimum_payment_amount = 10 # 0.10
default_maximum_payment_amount = 10000 # 100.00
default_number_of_payments = 500

# Set command line options:

descriptive_blurb = "Run a simple simulations using the agent set created " \
                  + "by the create_test_dataset.py script."
ap = argparse.ArgumentParser(description = descriptive_blurb)
ap.add_argument(
    "-i", "--input-filename", help = "Input filename",
    dest = "input_filename", action = "store",
    default = default_input_filename
)
ap.add_argument(
    "-o", "--output-filename", help = "Output filename",
    dest = "output_filename", action = "store",
    default = default_output_filename
)
ap.add_argument(
    "-P", "--number-of-payments", dest = "number_of_payments",
    action = "store", default = default_number_of_payments,
    help = "Number of payment iterations."
)
ap.add_argument(
    "-m", "--minimum-payment-amount", dest = "p_min", action = "store",
#    default = str(default_minimum_payment_amount),
    default = default_minimum_payment_amount,
    help = "Minimum random payment amount"
)
ap.add_argument(
    "-M", "--maximum-payment-amount", dest = "p_max", action = "store",
#    default = str(default_maximum_payment_amount),
    default = default_maximum_payment_amount,
    help = "Maximum random payment amount"
)
args = ap.parse_args()

input_filename = args.input_filename
output_filename = args.output_filename
p_min = int(args.p_min)
p_max = int(args.p_max)
number_of_payments = int(args.number_of_payments)

print(p_min)
print(p_max)
print(number_of_payments)

#-------------------------------------------------------------------------------

with open("temp/" + input_filename, "r") as f:
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

with open("temp/" + output_filename, "a") as f:
    for p in range(number_of_payments):
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

#        amount = random.randint(10, 10000)
        amount = random.randint(p_min, p_max)

        #payer_account_hrns = fph_to_hrns(payer_account_fph)
        #payee_account_hrns = fph_to_hrns(payee_account_fph)
        currency_fph = payee_account_currency_fph
        #currency_hrns = fph_to_hrns(payee_account_currency_fph)
        payer_identity_fph = payer_account_owner_fph
        #payer_identity_hrns = fph_to_hrns(payer_identity_fph)
        payee_identity_fph = payee_account_owner_fph
        #payee_identity_hrns = fph_to_hrns(payee_identity_fph)

        # A payment is recorded in the database:

        annotation = "Paid " + integer_to_money_s_format(amount) + " from " \
                   + fph_to_hrns(payer_account_owner_fph) + " to " \
                   + fph_to_hrns(payee_account_owner_fph)

        m = payment(payer_account_fph, payee_account_fph, amount, annotation)

        # A row is output to the payments file which will be used for the
        # construction of the GraphViz garphs and balance charts:

#        payment_row = payer_account_fph + ":" + payer_account_hrns + ":" \
#                    + payer_identity_fph + ":" + payer_identity_hrns + ":" \
#                    + payee_identity_fph + ":" + payee_identity_hrns + ":" \
#                    + payee_account_fph + ":" + payee_account_hrns + ":" \
#                    + currency_fph + ":" + currency_hrns + ":" \
#                    + integer_to_money_s_format(amount) + "\n"

        payment_row = payer_account_fph + ":" \
                    + payer_identity_fph + ":" \
                    + payee_account_fph + ":" \
                    + payee_identity_fph + ":" \
                    + currency_fph + ":" \
                    + integer_to_money_s_format(amount) + "\n"

        f.write(payment_row)
