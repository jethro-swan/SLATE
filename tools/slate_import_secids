#!/home/slate/SLATE/venv/bin/python3

import sys
import re

from app.core.slate_core import identify_entity, get_entity_type, new_secid
from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

#==============================================================================
# Bulk creation of *aliases* (*secids") from a CSV file with format:
#   secid name:parent namespace:primid
# e.g.
#   "js":"global.cc":"jw.gc.chep.mon.uk"
# Generally run over SSH as (e.g.):
#   cat <filename>.csv | ssh -p <port> <user>@<server> slate_import_secids
# where
#   filename.csv    is the name of the CSV file to be imported
#   user            is the SSH login name of a user with SLATE/NESTS access
#   port            is port number forwarded to a VM running SLATE/NESTS
# and  slate_import_secids  is this script, which sits somewhere easily
# found in the PATH (typically /usr/local/bin/).

re_secid_csv_line = re.compile(r'^(\".*\":){2}\".*\"$')

errors = []
secids_created = []
line_number = 0

for line in sys.stdin:
    if line.rstrip() == "q":
        sys.exit(1)
    if line == "":
        continue
    line_number += 1
    line_no = str(line_number).zfill(3) + ": "
    if line == "":
        continue
    if not re_secid_csv_line.match(line):
        errors.append(line_no + "ERROR: malformed input line")
        continue
    field = line.rstrip().split(":")
    secid_name = field[0].strip("\"")
    parent_ns = field[1].strip("\"")
    primid = field[2].strip("\"")

    parent_namespace_fph, \
    parent_namespace_hrns, \
    etype, \
    m = identify_entity(parent_ns)
    if m:
        errors.append(line_no + "ERROR: " + m)
    if parent_namespace_fph == "":
        errors.append(line_no + "ERROR: " + secid_name + " is not an entity")
    elif etype != "namespace":
        errors.append(
            line_no + parent_ns + " is " + etype + " (not a namespace)"
        )

    primid_fph, \
    primid_hrns, \
    etype, \
    m = identify_entity(primid)
    if m:
        errors.append(line_no + "ERROR: " + m)
    if primid_fph == "":
        errors.append(line_no + "ERROR: " + primid + " does not exist")
    elif etype != "primid":
        errors.append(
            line_no + "ERROR: " + primid + " is " + etype \
            + " (not a primary identity)"
        )

    secid_fph, \
    secid_hrns, \
    m = new_secid(
            secid_name,
            parent_namespace_fph,
            primid_fph
          )
    if m:
         errors.append(line_no + "ERROR: " + m)
    else:
        secids_created.append(
                               line_no + secid_fph + " > " + secid_hrns
                           )

print("\nAliases created:\n")
for secid in secids_created:
    print(secid)

print("\nErrors:\n")
for error in errors:
    print(error)
