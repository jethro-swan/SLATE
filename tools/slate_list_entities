#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import os
import pickle
from prettytable import PrettyTable
from app.core.constants import ENTITIES_DB
#from app.core.slate_core import get_entity_type, identify_entity
from app.core.slate_core import get_entity_types
from app.core.slate_core import identify_entity
from app.core.slate_core import get_account_properties
from app.core.slate_core import get_namespace_properties
from app.core.slate_core import get_currency_properties
#from app.core.slate_core import get_entity_common_properties
from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns

with sqlite3.connect(ENTITIES_DB) as conn:
    cursor = conn.cursor()
    # Retrieve the list of entities (FPH):
    cursor.execute("SELECT entity_fph FROM entities_registered")
    entities_list = cursor.fetchall()
    cursor.close()
if entities_list is None:
    print("Cannot retrieve entities")
    sys.exit(1)

entity_table = PrettyTable()
entity_table.align = "l"
entity_table.field_names = [
                             "entity HRNS",
                             "type",
                             "stewards | stewardships",
                             "currency (A|N)",
                             "owner (A|N|I)",
                             "private",
                             "active"
                           ]
table_rows = []

# For each FPH, entities of several distinct types may have been registered.
for entity in entities_list:
    entity_fph = entity[0]
    entity_types, m = get_entity_types(entity_fph) # list the types registered
    entity_hrns = fph_to_hrns(entity_fph)
    if m: # (this should never happen)
        print(m)
    for etype in entity_types:
        table_row = []  # a new row in the table is required for each entity
                        # type registered.
        # column 1:
        table_row.append(entity_hrns) # entity HRNS

        # column 2:
        table_row.append(etype) # entity type

        # column 3:
        if etype == "namespace": # stewarded
            active, \
            sandbox, \
            private, \
            namespace_owner_fph, \
            namespace_default_currency_fph, \
            namespace_stewards_list, \
            m = get_namespace_properties(entity_fph)
            stewards_sl = []
            for steward_fph in namespace_stewards_list:
                stewards_sl.append(fph_to_hrns(steward_fph))
            table_row.append(", ".join(stewards_sl))
        elif etype == "currency": # stewarded
            currency_fph, \
            currency_hrns, \
            active, \
            private, \
            sandbox, \
            prefix, \
            suffix, \
            default_account_name, \
            stewards_list, \
            m = get_currency_specific_properties(entity_fph)
            stewards_sl = []
            n_stewards = len(stewards_list)
            stewards_count = 0
            for steward_fph in stewards_list:
                stewards_sl.append(fph_to_hrns(steward_fph))
                stewards_count += 1
                if stewards_count < 2:
                    continue
                else:
                    stewards_sl.append("... (" + str(n_steward) + ")")
                    break
                stewards_sl.append(fph_to_hrns(steward_fph))
            table_row.append(", ".join(stewards_sl))
        elif etype == "primid":
            with sqlite3.connect(ENTITIES_DB) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT stewardships_fph_list FROM primids " \
                    + "WHERE entity_fph = ?", (entity_fph,)
                )
                result = cursor.fetchone()
                cursor.close()
            stewardships_list = pickle.loads(result[0])
            stewardships_sl = []
            n_stewardships = len(stewardships_list)
            stewardships_count = 0
            for stewardship_fph in stewardships_list:
                stewardships_sl.append(fph_to_hrns(stewardship_fph))
                stewardships_count += 1
                if stewardships_count < 2:
                    continue
                else:
                    stewardships_sl.append("... (" + str(n_stewardships) + ")")
                    break
                stewardships_sl.append(fph_to_hrns(stewardship_fph))
            table_row.append(", ".join(stewardships_sl))
        else:
            table_row.append("")

        # columns 4 and 5:
        if etype == "account":
            currency_fph, \
            owner_fph, \
            ahid_fph, \
            balance, \
            volume, \
            active, \
            m = get_account_specific_properties(entity_fph)
            account_owner_hrns = fph_to_hrns(owner_fph)
            account_currency_hrns = fph_to_hrns(currency_fph)
            table_row.append("A: " + account_currency_hrns)
            table_row.append("A: " + account_owner_hrns) # owner (*identity*)
        elif etype in ["namespace", "primid", "secid", "ahid"]:
            entity_fph, \
            parent_ns_fph, \
            m = get_entity_common_properties(entity_fph, etype)
            table_row.append("N: " + fph_to_hrns(currency_fph))
            if owner_fph:
                if etype == "namespace":
                    table_row.append("N: " + fph_to_hrns(owner_fph))
                else:
                    table_row.append("I: " + fph_to_hrns(owner_fph))
            else:
                table_row.append("")
#            table_row.append("")
        else:
            table_row.append("")
            table_row.append("")

        # column 6:
        if etype == "namespace":
            if private: # private?
                table_row.append("yes")
            else:
                table_row.append("no")
        else:
            table_row.append("")

        # column 7:
        if active: # active?
            table_row.append("yes")
        else:
            table_row.append("no")

#        print(str(len(table_row)) + " :: ", end="")
#        print(table_row)
        table_rows.append(table_row)

entity_table.add_rows(table_rows[0:])

print(entity_table)

print(
    "\n\n" \
    + "In the \"stewards | stewardships\" column:" \
    + "\n\n" \
    + "    If the entity type is an IDENTITY (a PRIMID or a SECID), the\n" \
    + "    first two items in a list of stewarded entities (stewardships)\n" \
    + "    is shown. If there are more than two (which will usually be the\n" \
    + "    case), a count of stewardhips is shown." \
    + "\n\n" \
    + "    If the entity is of a stewarded type (a NAMESPACE or CURRENCY),\n" \
    + "    the first two items in a list of stewards (PRIMIDS) is shown.\n" \
    + "    If there are more than two stewards (which will usually be the.\n" \
    + "    case), a count of stewards is shown.\n" \
    + "\n\n" \
    + "In the \"currency (A|N)\" column:" \
    + "\n\n" \
    + "    \"N\" indicates that this is the default CURRENCY of a NAMESPACE\n" \
    + "        (used in the creation of new ACCOUNTS within this NAMESPACE)."
    + "\n\n" \
    + "    \"A\" indicates that this is the CURRENCY of an ACCOUNT." \
    + "\n\n" \
    + "In the \"owner (A|N|I)\" column:" \
    + "\n\n" \
    + "    \"I\" indicates the owner of an IDENTITY serving as the root of\n" \
    + "        a private NAMESPACE tree (in which case it owns itself)." \
    + "\n\n" \
    + "    \"N\" indicates a NAMESPACE within such a private NAMESPACE tree." \
    + "\n\n" \
    + "    \"A\" indicates that this is the IDENTITY to which this ACCOUNT\n" \
    + "        belongs (its owner).\n\n"
)
