#!/home/john/NESTS/SLATE/venv/bin/python3

import sys
import re

from app.core.slate_core import identify_entity, get_entity_type
from app.core.slate_core import get_account_currency
from app.core.payments import payments
from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph
#from app.core.regexp_list import re_pvalue

#==============================================================================
# Bulk creation of *account*-to-*account* payments from a CSV file with format:
#   payer account:payee account:amount:annotation
# e.g.
#   "abc.def.gh.ij":"kl.mno.pq.rst":"76.50":"Some reasons"
# Generally run over SSH as (e.g.):
#   cat <filename>.csv | ssh -p <port> <user>@<server> slate_import_payments
# where
#   filename.csv    is the name of the CSV file to be imported
#   user            is the SSH login name of a user with SLATE/NESTS access
#   port            is port number forwarded to a VM running SLATE/NESTS
# and  slate_import_payments  is this script, which sits somewhere easily
# found in the PATH (typically /usr/local/bin/).

re_payment_csv_line = re.compile(r'^(\".*\":){3}\".*\"$')

errors = []
payments_made = []
line_number = 0

for line in sys.stdin:
    if line.rstrip() == "q":
        sys.exit(1)
    if line == "":
        continue
    line_number += 1
    line_no = str(line_number).zfill(3) + ": "
    if not re_payment_csv_line.match(line):
        errors.append(line_no + "ERROR: malformed input line")
        continue
    field = line.rstrip().split(":")
    payer_account = field[0].strip("\"")
    payee_account = field[1].strip("\"")
    amount = field[2].strip("\"").replace(",", "") # remove 000 separators
    annotation = field[3].strip("\"")

#    payer_account_fph, \
#    payer_account_hrns, \
#    payer_account_etype, \
#    m = identify_entity(payer_account)
#    if m:
#        errors.append(line_no + "ERROR: " + m)
#        continue
#    if payer_account_fph == "":
#        errors.append(line_no + "ERROR: " + payer_account + " not an entity")
#        continue
#    elif etype != "account":
#        errors.append(line_no + payer_account + " is not an account)")
#        continue

#    payee_account_fph, \
#    payee_account_hrns, \
#    payee_account_etype, \
#    m = identify_entity(payee_account)
#    if m:
#        errors.append(line_no + "ERROR: " + m)
#        continue
#    if payer_account_fph == "":
#        errors.append(line_no + "ERROR: " + payee_account + " not an entity")
#        continue
#    elif etype != "account":
#        errors.append(line_no + payer_account + " is not an account)")
#        continue

#    payer_currency_fph = get_account_currency(payer_account_fph)
#    payee_currency_fph = get_account_currency(payee_account_fph)
#    if payer_currency_fph !=  payee_currency_fph:
#        errors.append(line_no + "Payer and payee account currencies differ")
#        continue

#    if not re_pvalue.match(amount):
#        errors.append(line_no + "The amount is malformed")
#        continue

    # The payment will fail (returning an error message) if
    # - either *account* is invalid or inactive
    # - if the *accounts* are not in the same *currency*
    # - if the payment value is invalid (e.g. malformed)
    m = payment(payer_account_fph, payee_account_fph, amount, annotation)
    if m:
        errors.append(line_no + m)
        continue
    payments_made.append(line)



print("\nPayments made:\n")
for payment in payments_made:
    print(payment)

print("\nErrors:\n")
for error in errors:
    print(error)
