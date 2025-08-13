import sqlite3
import random
import os
import pickle
from pathlib import Path
from prettytable import PrettyTable
# see ttps://learnpython.com/blog/print-table-in-python/

from app.core.constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR

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
from app.core.slate_core import get_currency_properties
from app.core.slate_core import retrieve_pairing_account_fph

from app.core.messaging import send_message

from app.core.display import integer_to_money_format, integer_to_money_s_format

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

def payment(payer_account_fph, payee_account_fph, amount, annotation):

    payer_account_exists, \
    payer_account_active, \
    payer_account_currency_fph, \
    payer_account_owner_fph, \
    payer_account_ahid_fph, \
    payer_account_balance, \
    payer_volume, \
    m = account_status(payer_account_fph)
    if not payer_account_exists:
        return "Payer account " + payer_account_fph + " does not exist"
    if not payer_account_active:
        return "Payer account " + payer_account_fph + " is inactive"

    payee_account_exists, \
    payee_account_active, \
    payee_account_currency_fph, \
    payee_account_owner_fph, \
    payee_account_ahid_fph, \
    payee_account_balance, \
    payee_volume, \
    m = account_status(payee_account_fph)
    if not payee_account_exists:
        return "Payee account " + payee_account_fph + " does not exist"
    if not payee_account_active:
        return "Payee account " + payee_account_fph + " is inactive"

    if not re_pvalue.match(str(amount)):
        return str(amount) + " is not a valid payment"

    if payer_account_currency_fph != payee_account_currency_fph:
        return "Accounts " + payer_account_fph + " and " + payee_account_fph \
               + " are not in the same currency"

    #--------------------------------------------------------------------------
    # First the balances are adjusted:
    #
    payer_account_balance -= amount
    payee_account_balance += amount

    # Added 2025-03-18
    volume_increase = abs(amount)
    payer_volume += volume_increase
    payee_volume += volume_increase
    #
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # First the balances are adjusted:
        cursor.execute(
            """
            UPDATE accounts
            SET account_balance = ?, volume = ?
            WHERE entity_fph = ?
            """,
            (payer_account_balance, payer_volume, payer_account_fph)
        )
        cursor.execute(
            """
            UPDATE accounts
            SET account_balance = ?, volume = ?
            WHERE entity_fph = ?
            """,
            (payee_account_balance, payee_volume, payee_account_fph)
        )
        conn.commit()
        cursor.close()

    currency_fph, \
    currency_hrns, \
    active, \
    private, \
    sandbox, \
    prefix, \
    suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_properties(payer_account_currency_fph)

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
                payer_account_fph,
                payee_account_fph,
                currency_fph,
                amount,
                payer_account_balance,
                payee_account_balance,
                annotation
            )
        )
        conn.commit()
        cursor.close()

    payer_account_owner_hrns = fph_to_hrns(payer_account_owner_fph)
    payee_account_owner_hrns = fph_to_hrns(payee_account_owner_fph)

    subject_line = payer_account_owner_hrns

    message_body = annotation
    ## TO DO:
    # Add fields to table to accommodate the special case of payments:
    # e.g.
    #   payer_account
    #   payee_account
    #   currency
    #   amount
    #   annotation
    m = send_message(
            payment_timestamp,          # message timestamp
            payer_account_owner_fph,    # sender_id
            payee_account_owner_fph,    # recipient_id
            "payment",                  # category
            "",                         # subject prefix string
            subject_line,               # subject
            "",                         # stewardship_id (n/a)
            0,                          # longevity (indefinite)
            "",                         # expiry_datetime (no expiry)
            payer_account_fph,      # string
            payee_account_fph,      # string
            "",             # payer_ahid_fph unused in this mode
            "",             # payee_ahid_fph unused in this mode
            "",             # currency_fph unused in this mode
            amount,                     # integer
            message_body,               #
            False                       # indelibility
        )
#    if m:
#        print("Problem in  send_message( )  function")
#        print(m)

    return ""

#==============================================================================


#==============================================================================
# To make a payment using *ahid*|*currency* pairs

# Use of the *account*-to-*account* payment function (in app/core/payments.py)
# would require an inconvient number of modifications (for the messaging at
# least), so a modified version is used here.
#
# Make payment from one account to another (specified by FPH):

def ah_payment(
        payer_ahid_hrns,
        payee_ahid_hrns,
        currency_hrns,
        amount,
        annotation
    ):

    if payer_ahid_hrns == payee_ahid_hrns:
        return "An account cannot pay to itself"

    payer_account_fph, \
    payer_primid_fph, \
    m = retrieve_pairing_account_fph(payer_ahid_hrns, currency_hrns)
    if m:
        return m

    payee_account_fph, \
    payee_primid_fph, \
    m = retrieve_pairing_account_fph(payee_ahid_hrns, currency_hrns)
    if m:
        return m

    payer_account_exists, \
    payer_account_active, \
    payer_account_currency_fph, \
    payer_account_owner_fph, \
    payer_account_balance, \
    payer_volume, \
    m = account_status(payer_account_fph)
    if not payer_account_exists:
        return "Payer account " + payer_account_fph + " does not exist"
    if not payer_account_active:
        return "Payer account " + payer_account_fph + " is inactive"

    payee_account_exists, \
    payee_account_active, \
    payee_account_currency_fph, \
    payee_account_owner_fph, \
    payee_account_balance, \
    payee_volume, \
    m = account_status(payee_account_fph)
    if not payee_account_exists:
        return "Payee account " + payee_account_fph + " does not exist"
    if not payee_account_active:
        return "Payee account " + payee_account_fph + " is inactive"

    if not re_pvalue.match(str(amount)):
        return str(amount) + " is not a valid payment"

    #--------------------------------------------------------------------------
    # First the balances are adjusted:
    #
    payer_account_balance -= amount
    payee_account_balance += amount

    volume_increase = abs(amount)
    payer_volume += volume_increase
    payee_volume += volume_increase
    #
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # First the balances are adjusted:
        cursor.execute(
            "UPDATE accounts SET balance = ?, volume = ? WHERE entity_fph = ?",
            (payer_account_balance, payer_volume, payer_account_fph)
        )
        cursor.execute(
            "UPDATE accounts SET balance = ?, volume = ? WHERE entity_fph = ?",
            (payee_account_balance, payee_volume, payee_account_fph)
        )
        conn.commit()
        cursor.close()

    currency_fph, currency_hrns, active, private, sandbox, \
    prefix, suffix, default_account_name, \
    stewards_list, m = get_currency_properties(currency_hrns)

    #--------------------------------------------------------------------------
    # Then the payment is recorded in the journal:

    payer_ahid_fph, m = hrns_to_fph(payer_ahid_hrns)
    payee_ahid_fph, m = hrns_to_fph(payee_ahid_hrns)

    payment_timestamp = ledger_timestamp()

    #date_and_time = ledger_timestamp()
    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO payments (" \
            + "timestamp, " \
            + "payer_fph, " \
            + "payee_fph, " \
            + "currency_fph, " \
            + "amount, " \
            + "payer_balance, " \
            + "payee_balance, " \
            + "annotation" \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                payment_timestamp,
                payer_ahid_fph,     # The *ahid* and *account* FPH are stored
                payee_ahid_fph,     # in the same field (mode-dependent)
                currency_fph,
                amount,
                payer_account_balance,
                payee_account_balance,
                annotation
            )
        )
        conn.commit()
        cursor.close()

    payer_ahid_hrns = fph_to_hrns(payer_ahid_fph)
    payee_ahid_hrns = fph_to_hrns(payee_ahid_fph)

    subject_line = payer_ahid_hrns

    message_body = annotation
    ## TO DO:
    # Add fields to table to accommodate the special case of payments:
    # e.g.
    #   payer_account
    #   payee_account
    #   currency
    #   amount
    #   annotation
    m = send_message(
            payment_timestamp,          # message timestamp
            payer_ahid_fph,             # sender_id
            payee_ahid_fph,             # recipient_id
            "payment",                  # category
            "",                         # subject prefix string
            subject_line,               # subject
            "",                         # stewardship_id (n/a)
            0,                          # longevity (indefinite)
            "",                         # expiry_datetime (no expiry)
            "",          # string
            "",          # string
            payee_ahid_fph,             # string
            payee_ahid_fph,             # string
            currency_fph,               # string
            amount,                     # integer
            message_body,               #
            False                       # indelibility
        )
#    if m:
#        print("Problem in  send_message( )  function")
#        print(m)

    return ""

#==============================================================================
