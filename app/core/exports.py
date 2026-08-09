import sqlite3
import random
import os
import pickle
from pathlib import Path
from prettytable import PrettyTable
# see https://learnpython.com/blog/print-table-in-python/

from app.core.constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
#from .constants import SLATE_EXPORT, SLATE_IMPORT
#from constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from app.core.common import filename_timestamp as timestamp
from app.core.common import ledger_timestamp
from app.core.common import nshash

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps

from app.core.dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from app.core.dbm_functions import dbm_create_map

from app.core.auth import auth_hash

from app.core.regexp_list import *

from app.core.unix_functions import fcopy

from app.core.slate_core import account_status
from app.core.slate_core import list_currencies_in_common_by_fph
from app.core.slate_core import list_currencies_in_common_by_hrns
from app.core.slate_core import identify_entity
from app.core.slate_core import get_hub_mode
from app.core.slate_core import get_account_properties

#from app.core.display import integer_to_money_format
from app.core.display import integer_to_money_s_format

from app import app

#==============================================================================
# Create a list of payments made in the specified *currency*:

def list_currency_payments(currency_id):

    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if m:
        return [], m
    if not currency_fph:
        [], currency_id + "is not a registered identifier"
    if not ("currency" in etypes):
        return [], currency_hrns + " has no registered currency"

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified currency:
        cursor.execute(
            "SELECT " \
            + "timestamp, " \
            + "payment_id, " \
            + "payer_fph, " \
            + "payee_fph, " \
            + "amount, " \
            + "payer_balance, " \
            + "payee_balance, " \
            + "annotation " \
            + "FROM payments WHERE currency_fph = ?",
            (currency_fph,)
        )
        all_payments = cursor.fetchall()
        cursor.close()
    if all_payments is None:
        return [], ""
    #print("\nall_payments = ")
    #print(all_payments)
    #print()
    payments_list = []
    for p in all_payments:
#        print(p)
        payment_row = []
        timestamp = p[0]
        payment_id = str(p[1])
        payer_hrns = fph_to_hrns(p[2])          # *account* or *ahid*
        payee_hrns = fph_to_hrns(p[3])          # *account* or *ahid*
        amount = integer_to_money_s_format(p[4])
        payer_balance = integer_to_money_s_format(p[5])
        payee_balance = integer_to_money_s_format(p[6])
        annotation = p[7]
        if hub_mode == "slate":
            payment_row.append(currency_hrns)   # currency HRNS
        payment_row.append(payer_hrns)          # payer *ahid* HRNS
        payment_row.append(payee_hrns)          # payee  *ahid* HRNS
        payment_row.append(amount)              # amount paid
        payment_row.append(annotation)          # annotation
        payment_row.append(timestamp)           # timestamp
        payment_row.append(payment_id)          # payment number
        payment_row.append(payer_balance)       # payer balance
        payment_row.append(payee_balance)       # payee balance
        payments_list.append(payment_row)
    return payments_list, ""


#==============================================================================
# Create a list of payments made to or from the specified *account*:

def list_account_payments(account_id):
    account_fph, account_hrns, etypes, m = identify_entity(account_id)
    if m:
        return [], m
    if not account_fph:
        [], account_id + " is not a registered identifier"

    currency_fph, owner_fph, balance, volume, active, \
    account_type, account_category, account_units, \
    account_metrical_equivalence, account_dimensions, \
    m = get_account_properties(account_fph)

    owner_fph, owner_hrns, etypes, m = identify_entity(owner_fph)
    pair_indexed_account = directly_indexed_account = False
    if ("ahid" in etypes):
        # This is a *currency*|*ahid* pairing-identified *account* so the payer
        # or payee is displayed as the *ahid*'s identifier.
        pair_indexed_account = True
    elif ("account" in etypes):
        # This is a directly-addressed *account* so the payer or payee is
        # displayed as the *account*'s own identifier.
        directly_indexed_account = True
    else:
        return [], "Identifier " + account_hrns + " has no registered account"

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified currency:
        cursor.execute(
            "SELECT " \
            + "timestamp, " \
            + "payment_id, " \
            + "payer_fph, " \
            + "payee_fph, " \
            + "amount, " \
            + "payer_balance, " \
            + "payee_balance, " \
            + "annotation " \
            + "FROM payments " \
            + "WHERE (payer_fph = ? OR payee_fph = ?) and (currency_fph = ?)",
            (owner_fph, owner_fph, currency_fph)
       )
        all_payments = cursor.fetchall()
        cursor.close()

    if all_payments is None:
        return [], ""

    payments_list = []
    for payment in all_payments:
        p = list(payment)
        payment_row = []
        timestamp = p[0]
        payment_id = str(p[1]).zfill(8)
        payer_fph = p[2]
        payer_hrns = fph_to_hrns(payer_fph)
        payee_fph = p[3]
        payee_hrns = fph_to_hrns(payee_fph)
        amount = integer_to_money_s_format(p[4])
        payer_balance = integer_to_money_s_format(p[5])
        payee_balance = integer_to_money_s_format(p[6])
        annotation = p[7]
        payment_row.append(timestamp)
        payment_row.append(payment_id)
        if payee_fph == owner_fph: # credit
            payment_row.append(amount)          # amount received
            payment_row.append("")              # (no debit)
            payment_row.append(payer_hrns)      # received from
            payment_row.append(payee_balance)   # account balance
        elif payer_fph == owner_fph: # debit
            payment_row.append("")              # (no payment)
            payment_row.append(amount)          # amount paid
            payment_row.append(payee_hrns)      # paid to
            payment_row.append(payer_balance)   # balance account balance
        else:
            payment_row.append("")
            payment_row.append("")
            payment_row.append("")
            payment_row.append("")
        payment_row.append(annotation)          # annotation
        payments_list.append(payment_row)

    return payments_list, ""

#==============================================================================
# Export a CSV listing of all payments made in a specified *currency*
# (Complete and working)

def dump_currency_payments_csv(currency_id, show_header_row = True):

    SC = "," # add as argument later

    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if m:
        return "", m
    if not currency_fph:
        return "", currency_id + " is not a registered identifier"
    if not ("currency" in etypes):
        return "", currency_hrns + " has no registered currency"

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    payment_rows, m = list_currency_payments(currency_id)
    if m:
        return "", m

    csv_filename = "currency_" + fph_to_hrns(currency_fph) + "_journal_" \
                 + timestamp() + ".csv"
    csv_export_filepath = os.path.join(app.root_path, "export", csv_filename)
    with open(csv_export_filepath, "w") as csv_f:
        if show_header_row:
            if hub_mode == "slate":
               csv_f.write(
                    "currency" + SC \
                    + "payer" + SC \
                    + "payee" + SC \
                    + "amount" + SC \
                    + "annotation" + SC \
                    + "date and time" + SC \
                    + "payment number" + SC \
                    + "payer balance" + SC \
                    + "payee balance\n"
                )
            else:
                csv_f.write(
                    "date and time" + SC \
                    + "payment number" + SC \
                    + "payer HRNS" + SC \
                    + "payee HRNS" + SC \
                    + "amount" + SC \
                    + "annotation\n"
                )
        for row in payment_rows:
            csv_f.write(SC.join(row))
            csv_f.write("\n")

    return csv_filename, ""

#==============================================================================
# Export a CSV listing of all payments made to or from a specified *account*

def dump_account_payments_csv(account_id, show_header_row = False):

    SC = "," # add as argument later

    account_fph, account_hrns, etypes, m = identify_entity(account_id)
    if m:
        return "", m
    if not account_fph:
        return "", "The identifer " + account_id + " is not registered"
    if not ("account" in etypes):
        return "", "The identifer " + account_hrns + " has no account"

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    payment_rows, m = list_account_payments(account_id)
#    print(payment_rows)

    if hub_mode == "slate":
        currency_fph, owner_fph, balance, volume, active, \
        account_type, account_category, account_units, \
        account_metrical_equivalence, account_dimensions, \
        m = get_account_properties(account_fph)
        csv_filename = "account_" + fph_to_hrns(currency_fph) + "_"\
                     + fph_to_hrns(owner_fph) + "_journal_" \
                     + timestamp() + ".csv"
    else:
        csv_filename = "account_" + fph_to_hrns(account_fph) + "_journal_" \
                     + timestamp() + ".csv"

    csv_export_filepath = os.path.join(app.root_path, "export", csv_filename)
    with open(csv_export_filepath, "w") as csv_f:
        if show_header_row:
            csv_f.write(
                "date and time" + SC \
                + "payment number" + SC \
                + "credit" + SC \
                + "debit" + SC \
                + "other account" + SC \
                + "balance" + SC \
                + "annotation\n"
            )
        for row in payment_rows:

            for i in range(len(row)-1):
                csv_f.write(row[i])
                csv_f.write(SC)

            csv_f.write(row[-1])
            csv_f.write("\n")

    return csv_filename, ""

#------------------------------------------------------------------------------
def dump_currency_payments_html(currency_id):
    payment_rows, m = list_currency_payments(currency_id)
    if m:
        return "", m
    if len(payment_rows) == 0:
        return "", "Noting to return"

    html_str = "<table class=\"dump_table\">\n" \
             + "<tr>" \
             + "<th>currency</th>" \
             + "<th>payer</th>" \
             + "<th>payee</th>" \
             + "<th>amount</th>" \
             + "<th>annotation</th>" \
             + "</tr>\n"
    for row in payment_rows:
        print(row)
        if len(row) < 5:
            return "", "Short row"
        html_str += "<tr>"
        # payment ID:
        html_str += "<td>" + row[0] + "</td>"
        # payer HRNS (with link to FPH):
        html_str += "<td><a href=\"" + row[1] + "\">" \
                 + fph_to_hrns(row[1]) \
                 + "\"></td>"
        # payee HRNS (with link to FPH):
        html_str += "<td><a href=\"" + row[2] + "\">" \
                 + fph_to_hrns(row[2]) \
                 + "\"></td>"
        # amount paid
        html_str += "<td>" + row[3] + "></td>"
        # annotation
        html_str += "<td>" + row[4] + "></td>"
        html_str += "</tr>\n"
    html_str += "</table>\n"

#    if output_file_path and os.path.exists(output_file_path):
#        with open(output_file_path, "w") as html_f:
#            html_f.write(html_str)
#    else:
#        return "", "Output file path " + output_file_path + " does not exist"

    return html_str, ""

#==============================================================================
#

def dump_account_payments(account_fph):

    account_hrns = fph_to_hrns(account_fph)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()

        # Read transactions for specified currency:
        cursor.execute(
            "SELECT payment_id, payer_fph, payee_fph, amount, annotation " \
            + "FROM payments WHERE payer_fph = ? OR payee_fph = ?",
            (account_fph, account_fph)
        )
        results = cursor.fetchall()
        cursor.close()
        if results is None:
            return [], "No payments yet in currency " \
                       + fph_to_hrns(currency_hrns)
        #payments = list(results[0])
        payments = results
        all_payments = []
        for payment in payments:
            p = {}
            p["payment_id"] = str(payment[0]).zfill(6)
            p["payer_fph"] = payment[1]
            if isinstance(payment[1], str):
                p["payer_hrns"] = fph_to_hrns(payment[1])
            else:
                p["payer_hrns"] = "record corrupted"
            p["payee_fph"] = payment[2]
            if isinstance(payment[2], str):
                p["payee_hrns"] = fph_to_hrns(payment[2])
            p["amount"] = integer_to_money_s_format(payment[3])
            p["annotation"] = payment[4]
            all_payments.append(p)
        return all_payments, ""     # Returned as a list of dictionaries for
                                    # convenience of processin by Jinja2.

#==============================================================================
#

def dump_currency_payments(currency_id):

    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if m:
        return [], "Invalid currency"
    print("currency = " + currency_fph + " (" + currency_hrns + ")\n")

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()

        # Read transactions for specified currency:
        cursor.execute(
            "SELECT payment_id, payer_fph, payee_fph, amount, annotation " \
            + "FROM payments WHERE currency_fph = ?",
            (currency_fph,)
        )
        results = cursor.fetchall()
        cursor.close()
    if results is None:
        return [], "No payments yet in currency " + currency_hrns
    all_payments = []
    for payment in results:
        p = {}
        p["payment_id"] = results[0]
        p["payer_fph"] = results[1]
        p["payee_fph"] = results[2]
        p["amount"] = results[3]
        p["annotation"] = results[4]
        all_payments.append(p)
    return all_payments, ""     # Returned as a list of dictionaries for
                                    # convenience of processin by Jinja2.

#==============================================================================
##

def dump_currency_payments_table(currency_id):

    payments_list, m = list_currency_payments(currency_id)
    if m:
        print(m)
    else:
        ptable = PrettyTable()
        ptable.field_names = [
            "currency",
            "payer",
            "payee",
            "amount",
            "annotation",
            "timestammp",
            "payment ID",
            "payer balance",
            "payee balance"
        ]
        table_rows = payments_list
        ptable.add_rows(table_rows[0:])
        print(ptable)


#------------------------------------------------------------------------------
#def dump_currency_payments(currency_fph):

#    payments_table = dump_currency_payments_table(currency_fph)

#    return payments_table

#==============================================================================
