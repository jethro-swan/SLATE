#!/home/john/NESTS/SLATE/venv/bin/python3
#!/home/slate/SLATE/venv/bin/python3

import sys
import re

from app.core.slate_core import identify_entity, get_entity_type, new_account
from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

#==============================================================================
# Bulk creation of *accounts* from a CSV file with format:
#   account name:parent namespace:owner:currency
# e.g.
#   "kwh":"jw.gc.chep.mon.uk":"jw.chep.mon.uk":"kwh.gc.chep.mon.uk"
# Generally run over SSH as (e.g.):
#   cat <filename>.csv | ssh -p <port> <user>@<server> slate_import_accounts
# where
#   filename.csv    is the name of the CSV file to be imported
#   user            is the SSH login name of a user with SLATE/NESTS access
#   port            is port number forwarded to a VM running SLATE/NESTS
# and  slate_import_accounts  is this script, which sits somewhere easily
# found in the PATH (typically /usr/local/bin/).

re_account_csv_line = re.compile(r'^(\".*\":){3}\".*\"$')

errors = []
accounts_created = []
line_number = 0

for line in sys.stdin:
    if line.rstrip() == "q":
        sys.exit(1)
    if line == "":
        continue
    line_number += 1
    line_no = str(line_number).zfill(3) + ": "
    if not re_account_csv_line.match(line):
        errors.append(line_no + "ERROR: malformed input line")
        continue
    field = line.rstrip().split(":")
    account_name = field[0].strip("\"")
    parent_ns = field[1].strip("\"")
    owner = field[2].strip("\"")
    currency = field[3].strip("\"")

    parent_namespace_fph, \
    parent_namespace_hrns, \
    etype, \
    m = identify_entity(parent_ns)
    if m:
        errors.append(line_no + "ERROR: " + m)
    if parent_namespace_fph == "":
        errors.append(line_no + "ERROR: " + account_name + " is not an entity")
    elif etype != "namespace":
        errors.append(
            line_no + parent_ns + " is " + etype + " (not a namespace)"
        )

    owner_fph, \
    owner_hrns, \
    etype, \
    m = identify_entity(owner)
    if m:
        errors.append(line_no + "ERROR: " + m)
    if owner_fph == "":
        errors.append(line_no + "ERROR: " + owner + " is not an entity")
    elif (etype != "primid") and (etype != "secid"):
        errors.append(
            line_no + "ERROR: " + owner + " is " + etype \
            + " (not an identity)"
        )

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency)
    if m:
        errors.append(line_no + "ERROR: " + m)
    if currency_fph == "":
        errors.append(line_no + "ERROR: " + currency + " is not an entity")
    elif etype != "currency":
        errors.append(
            line_no + "ERROR: " + currency + " is " + etype + " (not currency)"
        )

    account_fph, \
    account_hrns, \
    m = new_account(
            account_name,
            parent_namespace_fph,
            owner_fph, # (Owner may be a *primid* or a *secid*)
            currency_fph
        )
    if m:
        errors.append(line_no + "ERROR: " + m)
    else:
        accounts_created.append(line_no + account_fph + " > " + account_hrns)

print("\nAccounts created:\n")
for account in accounts_created:
    print(account)

print("\nErrors:\n")
for error in errors:
    print(error)
