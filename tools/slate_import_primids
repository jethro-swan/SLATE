#!/home/slate/SLATE/venv/bin/python3

import sys
import re

from app.core.slate_core import identify_entity, get_entity_type, new_primid
from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph
from app.core.regexp_list import re_realname, re_email, re_password, re_pin


#==============================================================================
# Bulk creation of *primids* from a CSV file with format:
#   name:parent namespace:real name:email1:email2:password:PIN
# e.g.
#   "fred":gc.chep.mon.uk":"":"fred@dodgy.com":"":"bAdpA55w0rd":"314159"
# Generally run over SSH as (e.g.):
#   cat <filename>.csv | ssh -p <port> <user>@<server> slate_import_primids
# where
#   filename.csv    is the name of the CSV file to be imported
#   user            is the SSH login name of a user with SLATE/NESTS access
#   port            is port number forwarded to a VM running SLATE/NESTS
# and  slate_import_primids  is this script, which sits somewhere easily
# found in the PATH (typically /usr/local/bin/).

re_primid_csv_line = re.compile(r'^((\".*\":)|:){6}\".*\"$')


errors = []
primids_created = []
line_number = 0

for line in sys.stdin:
    if line.rstrip() == "q":
        sys.exit(1)
    if line == "":
        continue
    line_number += 1
    line_no = str(line_number).zfill(3) + ": "
    if not re_primid_csv_line.match(line):
        errors.append(line_no + "ERROR: malformed input line")
        continue
    field = line.rstrip().split(":")
    primid_name = field[0].strip("\"")
    parent_ns = field[1].strip("\"")
    real_name = field[2].strip("\"")
    if real_name:
        if not re_realname.match(real_name):
            errors.append(
                       line_no + "ERROR: real name " + real_name \
                       + " is invalid so has been discarded"
                   )
            real_name = ""
    email1 = field[3].strip("\"")
    if email1:
        if not re_email.match(email1):
            errors.append(line_no + "ERROR: email1 invalid")
            continue
    email2 = field[4].strip("\"")
    if email2:
        if not re_email.match(email2):
           errors.append(line_no + "ERROR: email2 invalid - ignored")
           email2 = ""
    password = field[5].strip("\"")
    if password == "":
        errors.append(line_no + "ERROR: no password provided")
        continue
#    elif not re_password.match(password):
#        errors.append(line_no + "ERROR: invalid password string")
#        continue
    pin = field[6].strip("\"")
    if pin == "":
        errors.append(line_no + "ERROR: no PIN provided")
        continue
    elif not re_pin.match(pin):
        errors.append(line_no + "ERROR: invalid PIN")
        continue

    parent_namespace_fph, \
    parent_namespace_hrns, \
    etype, \
    m = identify_entity(parent_ns)
    if m:
        errors.append(line_no + "ERROR: " + m)
    if parent_namespace_fph == "":
        errors.append(line_no + "ERROR: " + parent_ns + " is not an entity")
    elif etype != "namespace":
        errors.append(
            line_no + parent_ns + " is " + etype + " (not a namespace)"
        )

    primid_fph, \
    primid_hrns, \
    access_token, \
    m = new_primid(
            primid_name,
            parent_namespace_fph,
            real_name,
            email1,
            email2,
            password,
            pin
        )
    if m:
         errors.append(line_no + "ERROR: " + m)
    else:
        primids_created.append(
                               line_no + primid_fph + " > " + primid_hrns
                           )


print("\nLogin identities created:\n")
for primid in primids_created:
    print(primid)

print("\nErrors:\n")
for error in errors:
    print(error)
