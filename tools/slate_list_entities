#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import os
import pickle
from prettytable import PrettyTable
from app.core.constants import ENTITIES_DB
from app.core.slate_core import get_entity_types
from app.core.slate_core import identify_entity
from app.core.slate_core import get_account_properties
from app.core.slate_core import get_namespace_properties
from app.core.slate_core import get_currency_properties
from app.core.slate_core import get_primid_properties
from app.core.slate_core import get_ahid_properties
from app.core.slate_core import get_secid_properties
from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns

with sqlite3.connect(ENTITIES_DB) as conn:
    cursor = conn.cursor()
    # Retrieve the list of entities (FPH):
    cursor.execute("SELECT entity_fph FROM entities_registered")
    identifiers_list = cursor.fetchall()
    cursor.close()
if identifiers_list is None:
    print("Cannot retrieve entities")
    sys.exit(1)

print("="*150)
for identifier in identifiers_list:
    identifier_fph = identifier[0]
    print(identifier_fph + " > " + fph_to_hrns(identifier_fph))
    entity_types, m = get_entity_types(identifier_fph)
    print("entities registered: ", end="")
    print(entity_types)
    print("-"*150)






entity_table = PrettyTable()
entity_table.align = "l"
entity_table.field_names = [
                             "entity HRNS",
                             "entity FPH",
                             "type",
                             "stewards|hips",
                             "currency (A|N)",
                             "owner (A|P)"
                           ]
table_rows = []

# For each FPH, entities of several distinct types may have been registered.
for identifier in identifiers_list:
    identifier_fph = identifier[0]
    entity_types, m = get_entity_types(identifier_fph) # list types registered

    print("entities registered: ", end="")
    print(entity_types)

    identifier_hrns = fph_to_hrns(identifier_fph)
    if m: # (this should never happen)
        print(m)
    for etype in entity_types:

        print(">>> " + etype)

        table_row = []  # a new row in the table is required for each entity
                        # type registered for this

        # column 1: identifier HRNS
        table_row.append(identifier_hrns)

        # column 2: identifier FPH
        table_row.append(identifier_fph)

        # In preparation for columns 3, 5 and 6, we need to find the following:
        # - For column 3: the [active] or [private] state:
        #                 * private
        #                 % inactive/suspended
        # - For column 5: (A:) the CURRENCY of an ACCOUNT
        #                 (N:) the default CURRENCY of a NAMESPACE
        # - For column 6: the "owner" of the entity
        #                 (A:) the AHID or SECID to which an ACCOUNT belongs
        #                 (P:) the PRIMID to which an AHID or SECID belongs
        #
        if etype == "account":
            currency_fph, \
            owner_fph, \
            ahid_fph, \
            balance, \
            volume, \
            active, \
            m = get_account_properties(identifier_fph)
            owner_hrns = fph_to_hrns(owner_fph)
            currency_hrns = fph_to_hrns(currency_fph)
            private = False # n/a
        elif etype == "namespace":
            active, \
            sandbox, \
            private, \
            owner_fph, \
            currency_fph, \
            stewards_list, \
            m = get_namespace_properties(identifier_fph)
            owner_hrns = fph_to_hrns(owner_fph)
            currency_hrns = fph_to_hrns(currency_fph)
        elif etype == "ahid":
            active, \
            primid_fph, \
            accounts_fph_list, \
            m = get_ahid_properties(identifier_fph)
            private = False # n/a
            owner_hrns = fph_to_hrns(primid_fph)
            currency_hrns = "" # n/a
        elif etype == "primid":
            active, \
            administrator, \
            ahids_fph_list, \
            secids_fph_list, \
            pmap, \
            nstewardships_fph_list, \
            cstewardships_fph_list, \
            m = get_primid_properties(identifier_fph)
            owner_hrns = "" # n/a
            private = False # n/a
            currency_hrns = "" # n/a
        elif etype == "secid":
            active, \
            primid_fph, \
            accounts_fph_list, \
            m = get_secid_properties(identifier_fph)
            private = False
            currency_hrns = "" # n/a
            owner_hrns = fph_to_hrns(primid_fph)
        elif etype == "currency":
            currency_fph, \
            currency_hrns, \
            active, \
            private, \
            sandbox, \
            prefix, \
            suffix, \
            default_account_name, \
            currency_stewards_list, \
            m = get_currency_properties(identifier_fph)
            private = False # n/a
            currency_hrns = "" # n/a

        # column 3: entity type
        if etype == "namespace":
            rmsg = "namespace "
            if private:
                rmsg += " *"
            if not active:
                rmsg += " %"
            table_row.append(rmsg)
        else:
            table_row.append(etype)

        # column 4: number of stewards
        if etype == "namespace": # a stewarded entity
            active, \
            sandbox, \
            private, \
            namespace_owner_fph, \
            namespace_default_currency_fph, \
            namespace_stewards_list, \
            m = get_namespace_properties(identifier_fph)
            table_row.append("P:" + str(len(namespace_stewards_list)))
        elif etype == "currency": # a stewarded entity
            currency_fph, \
            currency_hrns, \
            active, \
            private, \
            sandbox, \
            prefix, \
            suffix, \
            default_account_name, \
            currency_stewards_list, \
            m = get_currency_properties(identifier_fph)
            table_row.append("P:" + str(len(currency_stewards_list)))
        elif etype == "primid":
            with sqlite3.connect(ENTITIES_DB) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT " \
                    + "nstewardships_fph_list " \
                    + "cstewardships_fph_list " \
                    + "FROM primids " \
                    + "WHERE entity_fph = ?", (identifier_fph,)
                )
                result = cursor.fetchone()
                cursor.close()
            if result is not None:
                nstewardships_list = pickle.loads(result[0])
                n_nstewardships = str(len(nstewardships_list))
                cstewardships_list = pickle.loads(result[0])
                n_cstewardships = str(len(cstewardships_list))
                table_row.append(
                    "N:" + str(len(nstewardships_list)) \
                    + " C:" + str(len(cstewardships_list))
                )
            else:
                table_row.append("")
        else:
            table_row.append("")

        # columns 5 and 6:
        if etype == "account":
            table_row.append("A: " + currency_hrns)
            table_row.append("A: " + owner_hrns) # owner (*identity*)
        elif etype == "namespace":
            table_row.append("N: " + fph_to_hrns(currency_fph))
            table_row.append("N: " + fph_to_hrns(owner_fph))
        elif etype == "ahid":
            table_row.append("I: " + fph_to_hrns(owner_fph))
            table_row.append("")
        else:
            table_row.append("")
            table_row.append("")

        table_rows.append(table_row)

    entity_table.add_rows(table_rows[0:])

print(entity_table)

print(
    "\n\n" \
    + "In the \"type\" column:" \
    + "\n\n" \
    + "    Each entity type registered for this identifier is listed in a" \
    + "    separate line.\n" \
    + "    * indicates a private NAMESPACE\n" \
    + "    % indicates an inactive (suspended) NAMESPACE, CURRENCY, PRIMID, " \
    + "    AHID, SECID or ACCOUNT\n" \
    + "\n\n" \
    + "In the \"stewards|hips\" column:" \
    + "\n\n" \
    + "    If the entity type is a PRIMID (PRIMARY IDENTITY), the number of" \
    + "    stewardships it holds will be shown with the prefix \"N:\" or" \
    + "    \"C:\" for NAMESPACES and CURRENCIES respectively.\n" \
    + "\n\n" \
    + "    If the entity is of a stewarded type (a NAMESPACE or CURRENCY),\n" \
    + "    the number of stewards (PRIMIDS) is shown with prefix \"P:\".\n" \
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
