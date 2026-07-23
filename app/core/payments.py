import sqlite3
import random
import os
import pickle
from pathlib import Path
from prettytable import PrettyTable
# see https://learnpython.com/blog/print-table-in-python/

from app.core.constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
from app.core.constants import ROBOTS_DB

from app.core.common import filename_timestamp as timestamp
from app.core.common import ledger_timestamp
from app.core.common import nshash

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps

from app.core.dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from app.core.dbm_functions import dbm_create_map

from app.core.auth import auth_hash

from app.core.regexp_list import *

from app.core.unix_functions import fcopy

#from app.core.slate_core import account_status
from app.core.slate_core import get_account_properties
from app.core.slate_core import list_currencies_in_common_by_fph
from app.core.slate_core import list_currencies_in_common_by_hrns
from app.core.slate_core import identify_entity
from app.core.slate_core import get_currency_properties
from app.core.slate_core import retrieve_pairing_account_fph
from app.core.slate_core import new_pairing
from app.core.slate_core import select_db_filepath
from app.core.slate_core import ahid_is_robot

from app.core.logging import log_event

#from app.core.robots import ahid_is_robot

from app.core.messaging import send_message

from app.core.display import integer_to_money_format, integer_to_money_s_format

from app import app

#==============================================================================
# Create the SQLite transactions database:

def create_payments_db(owner_fph):

    if os.path.exists(PAYMENTS_DB):
        # If the database exists already, it is deleted.
        os.remove(PAYMENTS_DB)
    conn = sqlite3.connect(PAYMENTS_DB)
    conn.execute("PRAGMA user_version;")
    conn.close()
    # set permissions to 660 (rw-rw----)
    os.chmod(PAYMENTS_DB, 0o660)

    ENTITIES_DB = select_db_filepath("payments", owner_fph)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Create payments table:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS payments (" \
            + "timestamp INTEGER TEXT NOT NULL, " \
            + "payment_id INTEGER PRIMARY KEY AUTOINCREMENT, " \
            + "payer_fph TEXT NOT NULL, " \
            + "payee_fph TEXT NOT NULL, " \
            + "currency_fph TEXT NOT NULL, " \
            + "amount INTEGER NOT NULL, " \
            + "payer_balance INTEGER NOT NULL, " \
            + "payee_balance INTEGER NOT NULL, " \
            + "annotation TEXT" \
            + ");"
        )
        conn.commit()
        cursor.close()


#==============================================================================
# Add to an *account* of type "count" (specified by FPH).
#
# *currency* type: scalar
# *currency* category: integer

def change_count(payer_fph, account_fph, amount, annotation):

    target_account_currency_fph, account_owner_fph, \
    account_balance, account_volume, account_active, \
    account_type, account_category, account_units, \
    account_metrical_equivalence, account_dimensions, \
    m = get_account_properties(account_fph)
    if m:
        return m
    if not account_active:
        return "Target account " + account_fph + " is inactive"

    active, administrator, \
    ahids_fph_list, accounts_fph_list, pmap, \
    nstewardships_fph_list, cstewardships_fph_list, \
    m = get_primid_properties(payer_id)
    if m:
        return m
    user_of_currency = False
    for account_fph in accounts_fph_list:
        currency_fph, m = get_account_currency(account_fph)
        if currency_fph == target_account_currency_fph:
            user_of_currency = True
            break
    if not user_of_currency:
        return "Invalid currency for this user"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # The payer balances are adjusted:
        cursor.execute(
            "UPDATE accounts SET account_balance = ?, volume = ? " \
            + "WHERE entity_fph = ?",
            (account_balance + amount, account_volume + amount, account_fph)
        )
        conn.commit()
        cursor.close()

    #--------------------------------------------------------------------------
    # Then the payment is recorded in the journal:

    payment_timestamp = ledger_timestamp()

    #date_and_time = ledger_timestamp()
    with sqlite3.connect(COUNTS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO counts (" \
            + "timestamp, " \
            + "payer_fph, " \
            + "payee_fph, " \
            + "currency_fph, " \
            + "amount, " \
            + "payee_balance, " \
            + "annotation " \
            + ") VALUES (?, ?, ?, ?, ?, ?)",
            (
                payment_timestamp,
                payee_account_fph,
                currency_fph,
                amount,
                payee_account_balance,
                annotation
            )
        )
        conn.commit()
        cursor.close()

    payee_account_owner_hrns = fph_to_hrns(payee_account_owner_fph)

#    subject_line = payer_account_owner_hrns

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
#            payer_account_owner_fph,    # sender_id
            payee_account_owner_fph,    # recipient_id
            "payment",                  # category
            "",                         # subject prefix string
            subject_line,               # subject
            "",                         # stewardship_id (n/a)
            0,                          # longevity (indefinite)
            "",                         # expiry_datetime (no expiry)
#            payer_account_fph,          # string
            payee_account_fph,          # string
            "",                         # payer_ahid_fph unused in this mode
            "",                         # payee_ahid_fph unused in this mode
            "",                         # currency_fph unused in this mode
            amount,                     # integer
            message_body,               #
            False,                      # indelibility
            False                       # broadcast
        )
#    if m:
#        print("Problem in  send_message( )  function")
#        print(m)

    return ""


def increase_count(payer_fph, account_fph, amount, annotation):
    if amount > 1:
        amount = 1
    return change_count(payer_fph, account_fph, amount, annotation)

def decrease_count(payer_fph, account_fph, amount, annotation):
    if amount > 1:
        amount = -1
    return change_count(payer_fph, account_fph, amount, annotation)






#==============================================================================
# Make payment from one *account* to another (specified by FPH).
#
# *currency* type: scalar
# *currency* category: money
#
# The *currency* type and *category* type are determined from the *account*s
# (both of which must be in the same *currency*).
#
# The *currency* type here is "zero_sum" (a.k.a. "money").

def payment(payer_account_fph, payee_account_fph, amount, annotation):

    payer_currency_fph, payer_account_owner_fph, \
    payer_account_balance, payer_account_volume, payer_account_active, \
    account_type, account_category, account_units, \
    account_metrical_equivalence, account_dimensions, \
    m = get_account_properties(payer_account_fph)
    if not payer_account_active:
        return "Payer account " + payer_account_fph + " is inactive"

    payee_currency_fph, payee_account_owner_fph, \
    payee_account_balance, payee_account_volume, payee_account_active, \
    account_type, account_category, account_units, \
    account_metrical_equivalence, account_dimensions, \
    m = get_account_properties(payee_account_fph)
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
    # CHANGE: This will have to be separated into two parts, using possibly
    # different ENTITIES_DB files for payer and payee ...

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # The payer balances are adjusted:
        cursor.execute(
            "UPDATE accounts SET account_balance = ?, volume = ? " \
            + "WHERE entity_fph = ?",
            (payer_account_balance, payer_volume, payer_account_fph)
        )
        conn.commit()
        cursor.close()

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # The payee balances is adjusted:
        cursor.execute(
            "UPDATE accounts SET account_balance = ?, volume = ? " \
            + "WHERE entity_fph = ?",
            (payee_account_balance, payee_volume, payee_account_fph)
        )
        conn.commit()
        cursor.close()

    currency_fph, currency_hrns, active, open, private, sandbox, \
    type, category, units, metrical_equivalence, dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(payer_account_currency_fph)

    #--------------------------------------------------------------------------
    # Then the payment is recorded in the journal:

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
            + "annotation " \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
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
            payer_account_fph,          # string
            payee_account_fph,          # string
            "",                         # payer_ahid_fph unused in this mode
            "",                         # payee_ahid_fph unused in this mode
            "",                         # currency_fph unused in this mode
            amount,                     # integer
            message_body,               #
            False,                      # indelibility
            False                       # broadcast
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
        payer_ahid_id,
        payee_ahid_id,
        currency_id,
        amount,
        annotation
    ):

    payer_ahid_fph, payer_ahid_hrns, etypes, \
    m = identify_entity(payer_ahid_id)

    payee_ahid_fph, payee_ahid_hrns, etypes, \
    m = identify_entity(payee_ahid_id)

    if not payer_ahid_fph:
        log_event(
            "tests", "non-existent payer",
            "Payer " + payer_ahid_id + " does not exist."
        )
        return "Payer ahid does not exist"

    if not payee_ahid_fph:
        log_event(
            "tests", "non-existent payee",
            "Payee " + payee_ahid_id + " does not exist."
        )
        return "Payee ahid does not exist"

    if payer_ahid_fph == payee_ahid_fph:
        log_event(
            "tests", "self-pay error",
            payer_ahid_hrns + " has attempted to make a payment to itself."
        )
        return "An ahid cannot pay to itself"

    currency_fph, currency_hrns, etypes, \
    m = identify_entity(currency_id)

    log_event(
        "tests", "payment made",
        "Payment of " + integer_to_money_s_format(amount) + " made by " \
        + payer_ahid_hrns + " to " + payee_ahid_hrns + " in " + currency_hrns
    )

    # If the robot *ahid* has not yet been paired with the *currency*, this
    # must be done before a payment can be made:
    if ahid_is_robot(payee_ahid_fph):
        with sqlite3.connect(ROBOTS_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT pairing_id FROM known_pairings " \
                + "WHERE ahid_fph = ? AND currency_fph = ?",
                (payee_ahid_fph, currency_fph)
            )
            result = cursor.fetchone()
            cursor.close()
        if result is None: # the pairing does not yet exist
            account_fph, account_hrns, \
            m = new_pairing("cc", payee_ahid_fph, currency_fph)

    payer_account_fph, payer_primid_fph, \
    m = retrieve_pairing_account_fph(payer_ahid_hrns, currency_hrns)
    if m:
        return m

    payee_account_fph, payee_primid_fph, \
    m = retrieve_pairing_account_fph(payee_ahid_hrns, currency_hrns)
    if m:
        return m

    payer_currency_fph, payer_account_owner_fph, \
    payer_account_balance, payer_account_volume, payer_account_active, \
    account_type, account_category, account_units, \
    account_metrical_equivalence, account_dimensions, \
    m = get_account_properties(payer_account_fph)
    if not payer_account_active:
        return "Payer account " + payer_account_fph + " is inactive"

    payee_currency_fph, payee_account_owner_fph, \
    payee_account_balance, payee_account_volume, payee_account_active, \
    account_type, account_category, account_units, \
    account_metrical_equivalence, account_dimensions, \
    m = get_account_properties(payee_account_fph)

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
    payer_account_volume += volume_increase
    payee_account_volume += volume_increase
    #
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # First the balances are adjusted:
        cursor.execute(
            "UPDATE accounts SET balance = ?, volume = ? WHERE entity_fph = ?",
            (payer_account_balance, payer_account_volume, payer_account_fph)
        )
        cursor.execute(
            "UPDATE accounts SET balance = ?, volume = ? WHERE entity_fph = ?",
            (payee_account_balance, payee_account_volume, payee_account_fph)
        )
        conn.commit()
        cursor.close()

    currency_fph, currency_hrns, active, open, private, sandbox, \
    type, category, units, metrical_equivalence, dimensions, \
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
            payment_timestamp,  # message timestamp
            payer_ahid_fph,     # sender_id
            payee_ahid_fph,     # recipient_id
            "payment",          # category
            "",                 # subject prefix string
            subject_line,       # subject
            "",                 # stewardship_id (n/a)
            0,                  # longevity (indefinite)
            "",                 # expiry_datetime (no expiry)
            "",                 # payer_account_fph
            "",                 # payer_ahid_fph
            payee_ahid_fph,     # string
            payee_ahid_fph,     # string
            currency_fph,       # string
            amount,             # integer
            message_body,       #
            False,              # indelibility
            False               # broadcast
        )
#    if m:
#        print("Problem in  send_message( )  function")
#        print(m)


    if ahid_is_robot(payee_ahid_fph):
        # The payment can now be recorded:
        with sqlite3.connect(ROBOTS_DB) as conn:
            cursor = conn.cursor()
            # Each payment received by a robot *ahid* is added here.
            cursor.execute(
                "INSERT INTO payments_received (" \
                + "robot_fph, " \
                + "payer_ahid_fph, " \
                + "currency_fph" \
                + ") VALUES (?, ?, ?)",
                (payer_ahid_fph, payee_ahid_fph, currency_fph)
            )
            conn.commit()
            cursor.close()

    return ""

#==============================================================================
