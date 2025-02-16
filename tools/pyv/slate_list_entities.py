#!/home/john/NESTS/SLATE/venv/bin/python3

import sqlite3
import os
import pickle
from prettytable import PrettyTable
from app.core.constants import ENTITIES_DB
from app.core.slate_core import get_entity_type, identify_entity
from app.core.slate_core import get_account_specific_properties
from app.core.slate_core import get_namespace_specific_properties
from app.core.slate_core import get_currency_specific_properties
from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns

with sqlite3.connect(ENTITIES_DB) as conn:
    cursor = conn.cursor()
    # Retrieve the list of *secids* for this *primid*:
    cursor.execute(
        """
        SELECT
            entity_fph,
            parent_namespace_fph,
            entity_type,
            default_currency_fph,
            private_namespace,
            namespace_owner_fph,
            active
        FROM entities_common
        """
    )
    entities_list = cursor.fetchall()
    cursor.close()

if entities_list is None:
    print("Cannot retrieve entities")
    sys.exit(1)

#for row in entities_list:
#    print(row)
#print()

entity_table = PrettyTable()
entity_table.align = "l"
entity_table.field_names = [
                             "entity HRNS",
                             "type",
                             "stewards | stewardships",
                             "currency (A|D)",
                             "owner (A|N)",
                             "private",
                             "active"
                           ]
table_rows = []
for entity in entities_list:
    table_row = []
    #table_row.append(entity[0])

    # column 1:
    table_row.append(fph_to_hrns(entity[0]))    # HRNS

    # column 2:
    table_row.append(entity[2])                 # type

    entity_type_1, m = get_entity_type(entity[0])
    if m:
        print(m)
    if entity_type_1 != entity[2]: # Check consistency
        print(
            "Entity type inconsistency 1 found: " + fph_to_hrns(entity[0]) \
            + "(" + entity_type_1 + "::" + entity[2] + ")"
        )
    entity_fph, \
    entity_hrns, \
    entity_type_2, \
    m = identify_entity(entity[0])
    if entity_type_1 != entity_type_1:
        print(
            "Entity type inconsistency 2 found: " + fph_to_hrns(entity[0]) \
            + "(" + entity_type_1 + "::" + entity_type_2 + ")"
        )

    # column 3:
    if entity_type_1 == "namespace": # stewarded
        default_currency_fph, \
        stewards_list, \
        sandbox, \
        m = get_namespace_specific_properties(entity[0])
        stewards_sl = []
        for steward_fph in stewards_list:
            stewards_sl.append(fph_to_hrns(steward_fph))
        table_row.append(", ".join(stewards_sl))
    elif entity_type_1 == "currency":
        currency_fph, \
        currency_hrns, \
        prefix, \
        suffix, \
        default_account_name, \
        stewards_list, \
        m = get_currency_specific_properties(entity[0])
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
    elif entity_type_1 == "primid":
        with sqlite3.connect(ENTITIES_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT stewardships_fph_list
                FROM primids
                WHERE entity_fph = ?
                """,
                (entity[0],)
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
        #print(stewardships_sl)
        #print(",".join(stewardships_sl))
        table_row.append(", ".join(stewardships_sl))
    else:
        table_row.append("")

    # columns 4 and 5:
    if entity_type_1 == "account":
        currency_fph, \
        owner_fph, \
        balance, \
        m = get_account_specific_properties(entity[0])
        account_owner_hrns = fph_to_hrns(owner_fph)
        account_currency_hrns = fph_to_hrns(currency_fph)
        table_row.append("A: " + account_currency_hrns)
        table_row.append("A: " + account_owner_hrns)  # owner (*identity*)
    elif entity_type_1 in ["namespace", "primid", "secid"]:
    #elif entity_type_1 == "namespace":
        table_row.append("N: " + fph_to_hrns(entity[3]))  # default *currency*
        table_row.append("N: " + fph_to_hrns(entity[5]))  # owner (*identity*)
#    elif entity_type_1 in ["primid", "secid"]:
#        table_row.append("n/a")
#        table_row.append("n/a")
    else:
        table_row.append("")
        table_row.append("")

    # column 6:
    if entity[4]:                               # private?
        table_row.append("yes")
    else:
        table_row.append("no")

    # column 7:
    if entity[6]:                               # active?
        table_row.append("yes")
    else:
        table_row.append("no")

    #print(table_row)
    table_rows.append(table_row)

entity_table.add_rows(table_rows[0:])



print(entity_table)
