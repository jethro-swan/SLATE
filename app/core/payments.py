import sqlite3
import random
import os
import pickle
from pathlib import Path
from prettytable import PrettyTable
# see ttps://learnpython.com/blog/print-table-in-python/

from constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
#from constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from common import filename_timestamp as timestamp
from common import nshash
from fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from dbm_functions import dbm_create_map
from auth import auth_hash
from regexp_list import *
from unix_functions import fcopy
from slate_core import account_exists
from slate_core import list_currencies_in_common_by_fph
from slate_core import list_currencies_in_common_by_hrns





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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                payer_fph TEXT NOT NULL,
                payee_fph TEXT NOT NULL,
                amount INTEGER NOT NULL,
                annotation TEXT
            );"""
        )

        conn.commit()
        cursor.close()

#==============================================================================
# Make payment from one account to another (specified by FPH):

def payment(payer_fph, payee_fph, amount, annotation):

    if not account_exists(payer_fph):
        return "Payer account " + payer_fph + " does not exist"
    if not account_active(payer_fph):
        return "Payer account " + payer_fph + " is inactive"
    if not account_exists(payee_fph):
        return "Payee account " + payee_fph + " does not exist"
    if not account_active(payee_fph):
        return "Payee account " + payee_fph + " is inactive"
    if not re_payment.match(amount):
        return str(amount) + " is not a valid payment"
    payee_currency = currency_of(payee_fph)
    if currency_of(payer_fph) != payee_currency:
        return "Accounts " + payer_fph + " and " + payee_fph + " are not in " \
               "the same currency"

    #--------------------------------------------------------------------------
    # First the balances are adjusted:
    #
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # First the balances are adjusted:
        #
        cursor.execute("""
            SELECT account_balance FROM accounts WHERE payee_fph = ?
            """,
            (payee_fph)
        )
        payee_balance = cursor.fetchone() + amount
        update_command = "UPDATE balance SET account_balance = " \
                       + str(payee_adjusted_balance) \
                       + "WHERE payee_fph = " + str(payee_fph)
        cursor.execute(update_command)
        #
        cursor.execute("""
            SELECT account_balance FROM accounts WHERE payer_fph = ?
            """,
            (payer_fph)
        )
        payer_adjusted_balance = cursor.fetchone() - amount
        update_command = "UPDATE balance SET account_balance = " \
                       + str(payer_adjusted_balance) \
                       + "WHERE payer_fph = " + str(payer_fph)
        cursor.execute(update_command)

        conn.commit()
        cursor.close()

    #--------------------------------------------------------------------------
    # Then the payment is recorded in the journal:
    #
    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()


        cursor.execute("""
            INSERT INTO payments (
                payer_fph, payee_fph, currency_fph, amount, annotation
            )
            VALUES (?, ?, ?, ?, ?)""",
            (payer_fph, payee_fph, currency_fph, amount, annotation)
        )

        conn.commit()
        cursor.close()

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


def dump_currency_payments(currency_fph, optype="csv", edtype="fph"):

    currency_hrns = fph_to_hrns(currency_fph)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()

        # Read transactions for specified currency:
        cursor.execute("""
            SELECT payment_id, payer_fph, payee_fph, amount, annotation
            FROM payments WHERE currency_fph = ?
            )
            VALUES (?)""",
            (currency_fph)
        )
        all_payments = cursor.fetchall()
        #conn.commit()
        cursor.close()

        payment_rows = []
        # Create column headers as the first row:
        payment_row.append(["payment number",
                            "payer FPH", "payer HRNS",
                            "payee FPH", "payee HRNS",
                            "amount",
                            "annotation"
                           ])
        for payment in all_payments:
            payment_row = []
            p = list(payment)
            payment_row.append(str(p[0]).zfill(8))       # payment number
            payment_row.append(p[1])                     # payer FPH
            payment_row.append(fph_to_hrns(payer_fph))   # payer HRNS
            payment_row.append(p[2])                     # payee FPH
            payment_row.append(fph_to_hrns(payee_fph))   # payee HRNS
            payment_row.append(str(p[3]//100))           # amount paid
            payment_row.append(p[4])                     # annotation
            payment_rows.append(payment_row)

        #----------------------------------------------------------------------
        if optype == "csv":
            # CSV header row:
            print("payment number:payer FPH:payee FPH:amount:annotation")
            for row in payment_rows:
                for row_field in row:
                    print(row_field + ":", end="")
                print() # add line feed

        #----------------------------------------------------------------------
        elif optype == "text_table":
            text_table = PrettyTable(payment_row[0])
            text_table.add_rows(payment_row[1:])
            print(text_table)

        #----------------------------------------------------------------------
        elif optype == "html":
            # HTML table header:
            print('<table class="dump_table">', end="")
            print('<tr>', end="")
            print('<th>payment number</th>', end="")
            print('<th>payer HRNS</th>', end="")
            print('<th>payer FPH</th>', end="")
            print('<th>payee HRNS</th>', end="")
            print('<th>payee FPH</th>', end="")
            print('<th>amount</th>', end="")
            print('<th>annotation</th>', end="")
            print('</tr>')
            for row in payment_rows:
                print('<tr>', end="")
                for row_field in row:
                    print('<td>' + row[row_field] + '</td>', end="")
                print('</tr>')
            print('</table>')

#==============================================================================

def dump_agent_payments(currency_fph, optype="csv", edtype="fph"):

    currency_hrns = fph_to_hrns(currency_fph)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()

        # Read transactions for specified currency:
        cursor.execute("""
            SELECT payment_id, payer_fph, payee_fph, currency_fph, amount,
            annotation FROM payments WHERE currency_fph = ?
            )
            VALUES (?)""",
            (currency_fph)
        )
        all_payments = cursor.fetchall()
        #conn.commit()
        cursor.close()


#==============================================================================
