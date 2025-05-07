#!/home/slate/SLATE/venv/bin/python3

import sys
import re

from app.core.slate_core import identify_entity, get_entity_type, new_namespace
from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

#==============================================================================
# Bulk creation of *namespaces* from a CSV file with format:
#   namespace names:parent namespace:initial steward:default currency
# e.g.
#   "gc":"chep.mon.uk":"jw.chep.mon.uk":"hrs.chep.mon.uk"
# Generally run over SSH as (e.g.):
#   cat <filename>.csv | ssh -p <port> <user>@<server> slate_import_namespaces
# where
#   filename.csv    is the name of the CSV file to be imported
#   user            is the SSH login name of a user with SLATE/NESTS access
#   port            is port number forwarded to a VM running SLATE/NESTS
# and  slate_import_namespaces  is this script, which sits somewhere easily
# found in the PATH (typically /usr/local/bin/).

re_namespace_csv_line = re.compile(r'^(\".*\":){3}\".*\"$')

errors = []
namespaces_created = []
line_number = 0

for line in sys.stdin:
    if line.rstrip() == "q":
        sys.exit(1)
    if line == "":
        continue
    line_number += 1
    line_no= str(line_number).zfill(3) + ": "
    if not re_namespace_csv_line.match(line):
        errors.append(line_no + "ERROR: malformed input line")
        continue
    field = line.rstrip().split(":")
    ns_name = field[0].strip("\"")
    parent_ns = field[1].strip("\"")
    steward1 = field[2].strip("\"")
    default_currency = field[3].strip("\"")

    parent_namespace_fph, \
    parent_namespace_hrns, \
    etype, \
    m = identify_entity(parent_ns)
#    print("parent_namespace_fph     = " + parent_namespace_fph)
#    print("parent_namespace_hrns    = " + parent_namespace_hrns)
#    print("etype                    = " + etype)
    if m:
        errors.append(line_no + "ERROR: " + m)
    if parent_namespace_fph == "":
        errors.append(line_no + "ERROR: " + ns_name + " is not an entity")
    elif etype != "namespace":
        errors.append(
            line_no + ns_name + " is " + etype + " (not a namespace)"
        )

    steward_fph, \
    steward_hrns, \
    etype, \
    m = identify_entity(steward1)
    if m:
        errors.append(line_no + "ERROR: " + m)
    if steward_fph == "":
        errors.append(line_no + "ERROR: " + steward1 + " is not an entity")
    elif etype != "primid":
        errors.append(
            line_no + "ERROR: " + steward1 + " is " + etype \
            + " (not a primary identity)"
        )

    default_currency_fph, \
    default_currency_hrns, \
    etype, \
    m = identify_entity(default_currency)
    if m:
        errors.append(line_no + "ERROR: " + m)
    if default_currency_fph == "":
        errors.append(
                   line_no + "ERROR: " + default_currency \
                   + " is not an entity"
               )
    elif etype != "currency":
        errors.append(
            line_no + "ERROR: " + default_currency + " is " + etype \
            + " (not a currency)"
        )

#    print(line_num)
#    print("\tns_name          = " + ns_name)
#    print("\tparent amespace  = " + parent_ns)
#    print("\tinitial steward  = " + steward1)
#    print("\tdefault currency = " + default_currency)

    namespace_fph, \
    namespace_hrns, \
    m = new_namespace(
            ns_name,
            parent_namespace_fph,
            default_currency_fph,
            steward_fph
        )
    if m:
         errors.append(line_no + "ERROR: " + m)
    else:
        namespaces_created.append(
                               line_no + namespace_fph + " > " + namespace_hrns
                           )


print("\nNamespaces created:\n")
for namespace in namespaces_created:
    print(namespace)

print("\nErrors:\n")
for error in errors:
    print(error)
