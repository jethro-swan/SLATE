import sqlite3
import random
import os
import pickle
from pathlib import Path
from prettytable import PrettyTable
# see ttps://learnpython.com/blog/print-table-in-python/

from .constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
#from .constants import SLATE_EXPORT, SLATE_IMPORT
#from constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP

from .common import filename_timestamp as timestamp
from .common import ledger_timestamp
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
from .slate_core import get_currency_specific_properties

from .messaging import send_message

from .display import integer_to_money_format

from app import app

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
                timestamp INTEGER TEXT NOT NULL,
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                payer_fph TEXT NOT NULL,
                payee_fph TEXT NOT NULL,
                currency_fph TEXT NOT NULL,
                amount INTEGER NOT NULL,
                payer_balance INTEGER NOT NULL,
                payee_balance INTEGER NOT NULL,
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

    currency_fph, \
    currency_hrns, \
    prefix, \
    suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_specific_properties(payer_currency_fph)


    #--------------------------------------------------------------------------
    # Then the payment is recorded in the journal:

    payment_timestamp = ledger_timestamp()

    #date_and_time = ledger_timestamp()
    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO payments (
                timestamp,
                payer_fph,
                payee_fph,
                currency_fph,
                amount,
                payer_balance,
                payee_balance,
                annotation
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payment_timestamp,
                payer_fph,
                payee_fph,
                currency_fph,
                amount,
                payer_balance,
                payee_balance,
                annotation
            )
        )
        conn.commit()
        cursor.close()

    subject_line = "from " + fph_to_hrns(payer_fph)

    message_body = "You have received a payment of " \
                 + prefix + str(amount) + suffix \
                 + " in currency " + currency_hrns \
                 + " from " + fph_to_hrns(payer_fph) \
                 + "\n"+ "="*40 + "\n" \
                 + annotation

    m = send_message(
            payment_timestamp,  # message timestamp
            payer_fph,          # sender_id
            payee_fph,          # recipient_id
            "payment",          # subject prefix string
            "payment received", # subject prefix string
            subject_line,       # subject
            "",                 # stewardship_id (n/a)
            0,                  # longevity (indefinite)
            "",                 # expiry_datetime (no expiry)
            message_body,       #
            False               # indelibility
        )
    if m:
        print("Problem in  send_message( )  function")
        print(m)





    return ""

#==============================================================================
















#==============================================================================
# Create a list of payments made in the specified *currency*:

def list_payments_in_currency(currency_identifier):

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_identifier)
    if m:
        return "", m
    if currency_fph == "":
        "", "No valid entity was specified"
    if etype != "currency":
        return "", "The entity specified is not a currency"

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified currency:
        cursor.execute(
            """
            SELECT timestamp,
                   payment_id,
                   payer_fph,
                   payee_fph,
                   amount,
                   payer_balance,
                   payee_balance,
                   annotation
            FROM payments
            WHERE currency_fph = ?
            """,
            (currency_fph,)
        )
        all_payments = cursor.fetchall()
        cursor.close()

    if all_payments is None:
        return [], ""

    payments_list = []
    for payment in all_payments:
        payment_row = []
        p = list(payment)
        payment_row.append(p[0])                            # timestamp
        payment_row.append(str(p[1]).zfill(8))              # payment number
        payment_row.append(fph_to_hrns(p[2]))               # payer HRNS
        payment_row.append(fph_to_hrns(p[3]))               # payee HRNS
        payment_row.append(integer_to_money_format(p[4]))   # amount paid
        payment_row.append(integer_to_money_format(p[5]))   # payer balance
        payment_row.append(integer_to_money_format(p[6]))   # payee balance
        payment_row.append(p[7])                            # annotation
#        print(payment_row)
        payments_list.append(payment_row)

    return payments_list, ""


#==============================================================================
# Create a list of payments made to or from the specified *account*:

# 2024-12-26 21:04 changing  []  to  {}  for Jinja2 iteration

def list_payments_for_account(account_identifier):

    account_fph, \
    account_hrns, \
    etype, \
    m = identify_entity(account_identifier)
    if m:
        return [], m
    if account_fph == "":
        [], "No valid entity was specified"
    if etype != "account":
        return [], "The entity specified is not an account"

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified currency:
        cursor.execute(
            """
            SELECT timestamp,
                   payment_id,
                   payer_fph,
                   payee_fph,
                   amount,
                   payer_balance,
                   payee_balance,
                   annotation
            FROM payments
            WHERE payer_fph = ? OR payee_fph = ?
            """,
            (account_fph, account_fph)
        )
        all_payments = cursor.fetchall()
        cursor.close()
    if all_payments is None:
        return [], ""

    payments_list = []
    for payment in all_payments:
        payment_row =[]
        p = list(payment)
        payment_row.append(p[0])
        payment_row.append(str(p[1]).zfill(8))
        # If THIS *account* is the payee, put the amount in the recipts
        # column (3) and leave the payments column blank:
        if p[3] == account_fph:
            payment_row.append(integer_to_money_format(p[4])) # amount
            payment_row.append("")
            payment_row.append(p[2]) # payee HRNS
            payment_row.append(integer_to_money_format(p[6])) # balance
        elif p[2] == account_fph:
            payment_row.append("")
            payment_row.append(integer_to_money_format(p[4])) # amount
            payment_row.append(p[3]) # payer HRNS
            payment_row.append(integer_to_money_format(p[5])) # balance
        else:
            payment_row.append("")
            payment_row.append("")
            payment_row.append("")
            payment_row.append("")
        payment_row.append(p[7]) # annotation
        payments_list.append(payment_row)

    return payments_list, ""







#==============================================================================
# Export a CSV listing of all payments made in a specified *currency*
# (Complete and working)

def dump_currency_payments_csv(
        currency_identifier,
        show_header_row = True
    ):
    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_identifier)
    if m:
        return "", m
    if etype != "currency":
        return "", "The entity specified is not a currency"
    if currency_fph == "":
        return "", "No valid currency was specified"

    csv_filename = "currency_" + currency_fph \
                 + "_journal_" + timestamp() + ".csv"

    csv_export_filepath = os.path.join(app.root_path, "export", csv_filename)

    payment_rows, m = list_payments_in_currency(currency_identifier)
    if m:
        print("m = " + m)
        return "", m

    with open(csv_export_filepath, "w") as csv_f:
        if show_header_row:
            csv_f.write(
                      "date and time\t"
                      + "payment number\t" \
                      + "payer HRNS\t" \
                      + "payee HRNS\t" \
                      + "amount\t" \
                      + "annotation\n"
                  )
        for row in payment_rows:
            csv_f.write("\t".join(row))
            csv_f.write("\n")

    return csv_export_filepath, ""

#==============================================================================
# Export a CSV listing of all payments made to or from a specified *account*


def dump_account_payments_csv(
        account_identifier,
        show_header_row = False
    ):
    account_fph, \
    account_hrns, \
    etype, \
    m = identify_entity(account_identifier)
    if m:
        return "", m
    if etype != "account":
        return "", "The entity specified is not an account"
    if account_fph == "":
        return "", "No valid account was specified"

    csv_filename = "account_" + account_fph \
                 + "_journal_" + timestamp() + ".csv"

    csv_export_filepath = os.path.join(app.root_path, "export", csv_filename)

    payment_rows, m = list_payments_for_account(account_identifier)
    if m:
        return [], m

    with open(csv_export_filepath, "w") as csv_f:
#        if show_header_row:
#            csv_f.write(
#                      "date and time\t" \
#                      + "payment number\t" \
#                      + "credit\t" \
#                      + "debit\t" \
#                      + "other account\t" \
#                      + "balance\t" \
#                      + "annotation\n"
#                  )
        for row in payment_rows:
            for i in range(len(row)-1):
                csv_f.write(row[i])
                csv_f.write("\t")
            csv_f.write(row[-1])
            csv_f.write("\n")

    return csv_filename, ""















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
