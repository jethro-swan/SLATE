import sqlite3
import random
import os
import pickle
from pathlib import Path
from prettytable import PrettyTable
# see ttps://learnpython.com/blog/print-table-in-python/

from .constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
#from constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from .common import filename_timestamp as timestamp
from .common import nshash
from .fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from .dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from .dbm_functions import dbm_create_map
from .auth import auth_hash
from .regexp_list import *
from .unix_functions import fcopy
from .slate_core import account_status
from .slate_core import list_currencies_in_common_by_fph
from .slate_core import list_currencies_in_common_by_hrns
from .slate_core import identify_entity
from .display import integer_to_money_format


#==============================================================================
# Create the SQLite transactions database:

def create_payments_db():

    if os.path.exists(PAYMENTS_DB):
        # If the database exists already, it is deleted after a time-stamped
        # copy has been saved.
        fcopy(PAYMENTS_DB, DB_BKP_DIR + '/payments_' + timestamp() + '.db')
        os.remove(PAYMENTS_DB)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Create payments table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                payer_fph TEXT NOT NULL,
                payee_fph TEXT NOT NULL,
                currency_fph TEXT NOT NULL,
                amount INTEGER NOT NULL,
                annotation TEXT
            );
            """
        )
        conn.commit()
        cursor.close()

#==============================================================================
# Make payment from one account to another (specified by FPH):

def payment(payer_fph, payee_fph, amount, annotation):

    payer_exists, \
    payer_active, \
    payer_currency_fph, \
    payer_account_owner_fph, \
    payer_balance, m = account_status(payer_fph)
    if not payer_exists:
        return "Payer account " + payer_fph + " does not exist"
    if not payer_active:
        return "Payer account " + payer_fph + " is inactive"

    payee_exists, \
    payee_active, \
    payee_currency_fph, \
    payee_account_owner_fph, \
    payee_balance, m = account_status(payee_fph)
    if not payee_exists:
        return "Payee account " + payee_fph + " does not exist"
    if not payee_active:
        return "Payee account " + payee_fph + " is inactive"

    if not re_pvalue.match(str(amount)):
        return str(amount) + " is not a valid payment"

    if payer_currency_fph != payee_currency_fph:
        return "Accounts " + payer_fph + " and " + payee_fph + " are not in " \
               "the same currency"

    #--------------------------------------------------------------------------
    # First the balances are adjusted:
    #
    payer_balance -= amount
    payee_balance += amount
    #
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # First the balances are adjusted:
        cursor.execute(
            "UPDATE accounts SET account_balance = ? WHERE entity_fph = ?",
            (payer_balance, payer_fph)
        )
        cursor.execute(
            "UPDATE accounts SET account_balance = ? WHERE entity_fph = ?",
            (payee_balance, payee_fph)
        )
        conn.commit()
        cursor.close()

    #--------------------------------------------------------------------------
    # Then the payment is recorded in the journal:

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payments (
                payer_fph,
                payee_fph,
                currency_fph,
                amount,
                annotation
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payer_fph,
                payee_fph,
                payer_currency_fph,
                amount,
                annotation
            )
        )
        conn.commit()
        cursor.close()

    return ""

#==============================================================================





# TEMPORARY FAKE pending relocation to Flask SWI code:
def url_for(whatever):
    return ""

def list_currencies_in_common_as_html(a1_fph, a2_fph):
    print("<ul>")
    for currency_fph in list_currencies_in_common_by_fph(a1_fph, a2_fph):
        print(
            "<li><a href=\"" + url_for("something") + "\">" \
            + fph_to_hrns(currency_fph) + "</a></li>"
        )
    print("</ul>")




#==============================================================================


def list_payments_in_currency(currency_identifier):

    currency_fph, \
    currency_hrns, \
    entity_type, \
    m = identify_entity(currency_identifier)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified currency:
        cursor.execute(
            """
            SELECT payment_id, payer_fph, payee_fph, amount, annotation
            FROM payments
            WHERE currency_fph = ?
            """,
            (currency_fph,)
        )
        all_payments = cursor.fetchall()
        cursor.close()

    if all_payments is None:
        return []

    payments_list = []
    # Create column headers as the first row:
    for payment in all_payments:
        payment_row = []
        #p = payment
        p = list(payment)
        #print(p)
        payment_row.append(str(p[0]).zfill(8))              # payment number
        payment_row.append(p[1])                            # payer FPH
        #payment_row.append(fph_to_hrns(p[1]))               # payer HRNS
        payment_row.append(p[2])                            # payee FPH
        #payment_row.append(fph_to_hrns(p[2]))               # payee HRNS
        payment_row.append(integer_to_money_format(p[3]))   # amount paid
        payment_row.append(p[4])                            # annotation
        #print(payment_row)
        payments_list.append(payment_row)
    #print("***** End of loop *****")
    #print(payments_list)
    return payments_list

#------------------------------------------------------------------------------
def dump_currency_payments_csv(currency_identifier, output_file_path):
    payment_rows = list_payments_in_currency(currency_identifier)
    if output_file_path and os.path.exists(output_file_path):
        with open(output_file_path, "w") as csv_f:
            csv_f.write("payment number:payer FPH:payee FPH:amount:annotation")
            for row in payment_rows:
                csv_f.write(":".join(row))
    return payment_rows

#==============================================================================
##

def dump_currency_payments_table(currency_identifier, output_file_path):

    payment_rows = list_payments_in_currency(currency_identifier)
    payments_table = PrettyTable()
    #print(payments_table)
    payments_table.align = "l"
    payments_table.field_names = [
                                    "payment number",
                                    "payer HRNS",
                                    "payee HRNS",
                                    "amount",
                                    "annotation"
                                 ]
    table_rows = []
    for row in payment_rows:
        table_row = []
        table_row.append(row[0])                        # payment ID
        table_row.append(fph_to_hrns(row[1]))           # payer HRNS
        table_row.append(fph_to_hrns(row[2]))           # payee HRNS
        table_row.append(row[3])                        # amount paid
        table_row.append(row[4])                        # annotation
        table_rows.append(table_row)

    payments_table.add_rows(table_rows[1:])



    if output_file_path and os.path.exists(output_file_path):
        with open(output_file_path, "w") as table_f:
            table_f.write(text_table)

    return payments_table

#------------------------------------------------------------------------------
def dump_currency_payments(currency_fph):

    payments_table = dump_currency_payments_table(currency_fph)

    return

#------------------------------------------------------------------------------
def dump_currency_payments_html(currency_identifier, output_file_path):
    payment_rows = list_payments_in_currency(currency_identifier)

    html_str = "<table class=\"dump_table\">\n" \
             + "<tr>" \
             + "<th>payment number</th>" \
             + "<th>payer HRNS</th>" \
             + "<th>payee HRNS</th>" \
             + "<th>amount</th>" \
             + "<th>annotation</th>" \
             + "</tr>\n"
    for row in payment_rows:
        html_str = []
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

    if output_file_path and os.path.exists(output_file_path):
        with open(output_file_path, "w") as html_f:
            html_f.write(html_str)

    return html_str

#==============================================================================
#

def dump_account_payments(account_fph):

    account_hrns = fph_to_hrns(account_fph)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()

        # Read transactions for specified currency:
        cursor.execute(
            """
            SELECT payment_id, payer_fph, payee_fph, amount, annotation
            FROM payments
            WHERE payer_fph = ? OR payee_fph = ?
            """,
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
            #print("Payments history")
            #for i in range(len(payments)):
            #    print(payments[i])
            #print()
            #if account_fph == payments[1]:
            #    p["direction"] = "payment"
            #elif account_fph == payments[2]:
            #    p["direction"] = "receipt"
            #else:
            #    p["direction"] = "gremlin alert" # something very wrong
            p["payment_id"] = str(payment[0]).zfill(6)
            p["payer_fph"] = payment[1]
            if isinstance(payment[1], str):
                p["payer_hrns"] = fph_to_hrns(payment[1])
            else:
                p["payer_hrns"] = "record corrupted"
            p["payee_fph"] = payment[2]
            if isinstance(payment[2], str):
                p["payee_hrns"] = fph_to_hrns(payment[2])
            p["amount"] = integer_to_money_format(payment[3])
            p["annotation"] = payment[4]
            all_payments.append(p)
        return all_payments, ""     # Returned as a list of dictionaries for
                                    # convenience of processin by Jinja2.

#==============================================================================
#

def dump_currency_payments(currency_fph):

    currency_hrns = fph_to_hrns(currency_fph)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()

        # Read transactions for specified currency:
        cursor.execute(
            """
            SELECT payment_id, payer_fph, payee_fph, amount, annotation
            FROM payments
            WHERE currency_fph = ?
            """,
            (currency_fph,)
        )
        payments = cursor.fetchall()
        cursor.close()
        if payments is None:
            return [], "No payments yet in currency " + currency_hrns
        all_payments = []
        for payment in payments:
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
