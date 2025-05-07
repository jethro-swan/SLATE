#!/home/slate/SLATE/venv/bin/python3

# This file contains functions to emulate the "traditional" OM mode pairing a
# re-useable *account_holder* identifier with a *currency* identifier.
#
# On the surface, the bahaviour is a little different from that of the
# SLATE/NESTS approach in that the *account* created to represent the pairing
# is only ever identified (to most users in "om_trad" mode) indirectly by
# *account_holder* and *currency*.

# The account_holder_hrns and currency_hrns are entered in a form.
# These are used to create a new pairing which maps to a new *account*.

# The *account_holder* HRNS can be retrieved by FPH in the same way as any
# other entity type.

# Each *primid* maintains a map of *pairings* as a dictionary of lists:
#
#   account_holder_hrns: [currency1_fph, currency2_fph, ...]
#
#
#=============================================================================

import sqlite3
import random
import os
import pickle

from app.core.regexp_list import re_hrns, re_fph
from app.core.slate_core import hrns_to_fph, fph_to_hrns
from app.core.slate_core import add_entity_common_properties
from app.core.slate_core import new_account
from app.core.slate_core import identify_entity



#=============================================================================

def split_hrns(identifier_hrns):
    if not re_hrns.match(identifier_hrns):
        return "", ""
    names = identifier_hrns.split(".")
    name = names.pop(0)
    parent_namespace_hrns = ".".join(names)
    return name, parent_namespace_hrns


#=============================================================================

def retrieve_pmap(owner_primid_identifier):

    owner_fph, \
    owner_hrns, \
    owner_type, \
    m = identify_entity(owner_primid_identifier)
    if (owner_type != "primid"):
        return {}, owner_primid_identifier + " is not a primid"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT pmap FROM primids WHERE entity_fph = ?",
            (owner_fph,)
        )
        result = cursor.fetchone()
        # If no pmap exists yet, it is created:
        if result is None:
            cursor.execute(
                "UPDATE primids SET pmap = ? WHERE entity_fph = ?",
                (owner_fph, pickle.dumps({}))
            )
            conn.commit()
            cursor.close()
            return {}, ""
        else:
            pmap = pickle.loads(result)
            cursor.close()
        return pmap, ""     # dictionary of  account_holder_hrns:currency_hrns
                            # pairs for display in table.


#=============================================================================

def create_new_pairing(
        owner_primid_identifier,    # HRNS or FPH
        account_holder_hrns,        # HRNS
        currency_hrns               # HRNS
    ):

    # The *currency* and owner *primid* are validated before proceeding to
    # create a new *account-holder*. Only if both exist will a new *account*
    # or *account-holder* be created.

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_hrns)
    if (etype != "currency"):
        return "", currency_fph + " is not a currency"

    owner_fph, \
    owner_hrns, \
    owner_type, \
    m = identify_entity(owner_primid_identifier)
    if (owner_type != "primid"):
        return "", owner_primid_identifier + " is not a primid"

    # If the *account-holder* does not exist already it must be created:
    #
    account_holder_fph, \
    account_holder_hrns, \
    etype, \
    m = identify_entity(account_holder_hrns)
    if m:
        return "", m
    if account_holder_fph == "": # does not exist

        account_holder_name, parent_hrns = split_hrns(account_holder_hrns)

        parent_namespace_fph, \
        parent_namespace_hrns, \
        etype, \
        m = identify_entity(parent_hrns)
        if m:
            return "", m

        if not re_hrns.match(parent_namespace_hrns):
            return "", "Invalid parent namespace: " + parent_namespace_hrns

        # The *account_holder* is added to the HRNS>FPH and FPH>HRNS maps:
        #
        account_holder_fph, m = hrns_to_fph(account_holder_hrns)

        # The *account_holder* is then added to the entities_common table.
        # (Unlike other entity types, *account_holder* has no table for
        # specific properties.)
        #
        add_entity_common_properties(
            account_holder_fph,
            parent_namespace_fph,
            "account_holder",
            "",         # n/a
            False,      # not applicable to *pairing*
            owner_fph,
            True
        )

    # At this point, whether or not it has been necessary to create it, we now
    # have both the HRNS and the FPH of the *account_holder*. It can now be
    # paired with the specified *currency* to index a new *account*.

    # The *account* created for this *account-holder"|*currency* pairing will
    # not usually be seen by its owner, but it still needs an HRNS. To insure
    # that it is both unique and easily related to the two components of the
    # pairing. Therefore its name is constructed from the two:
    #
    ah_id = "_".join(currency_hrns.split("."))
    c_id = "_".join(account_holder_hrns.split("."))
    account_name = "_".join([ah_id, "_P_", c_id])
    #
    # This name is then prefixed to the root of the owner *primid*'s private
    # *namespace*.
    #
    account_fph, \
    account_hrns, \
    m = new_account(
            account_name,
            owner_fph,
            owner_fph,
            currency_fph
        )

    # The *account_holder* may be paired with any *currency* (once only). These
    # serve as the co-ordinates in a grid identifying the *account* created
    # above.
    #
    # If a *pairing* entity does not exist already it is created.
    #
    # The pairings dictionary is retrieved. If none exists, an empty
    pmap, m = retrieve_pmap(owner_primid_identifier)

    pmap[account_holder_hrns] = {}
    pmap[account_holder_hrns][currency_hrns] = account_fph
    #pmap[account_holder_hrns][currency_hrns] = account_fph

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE primids SET pmap = ? WHERE entity_fph = ?",
            (owner_fph, pickle.dumps(pmap))
        )
        conn.commit()
        cursor.close()

    return account_fph

#=============================================================================



#=============================================================================

def retrieve_pairing_account_fph(
        account_holder_hrns,    # HRNS
        currency_identifier     # HRNS or FPH
    ):

    if not re_hrns.match(account_holder_hrns):
        return "", "", account_holder_hrns + " is not an account-holder"

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_identifier)
    if (etype != "currency"):
        return "", "", currency_fph + " is not a currency"

    primid_fph = identify_account_holder_primid(account_holder_hrns)

    ah_currency_map = get_ah_currency_map(primid_fph)

    if ah_currency_map[account_holder_hrns] is None:
        return "", "", account_holder_hrns + " is not an account-holder"

    if ah_currency_map[account_holder_hrns][currency_hrns] is None:
        return "", account_holder_hrns \
                   + " does not have use of currency " + currency_hrns
    else:
        account_fph = ah_currency_map[account_holder_hrns][currency_hrns]

    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(account_hrns)
    if m:
        return "", "", m
    elif etype != "account":
        return "", "", "Error: entity is not account" # should be impossible

    return account_fph, primid_fph, ""


#=============================================================================


#==============================================================================
# To make a payment using

# Use of the *account*-to-*account* payment function (in app/core/payments.py)
# would require an inconvient number of modifications (for the messaging at
# least), so a modified version is used here.
#
# Make payment from one account to another (specified by FPH):

def ah_payment(
        payer_account_holder_hrns,
        payee_account_holder_hrns,
        currency_hrns,
        amount,
        annotation
    ):

    # Identify the
    #   payer_account_fph
    #   payee_account_fph
    # from the arguments submitted.

    #payer_account_fph
    #payee_account_fph


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
    prefix, \
    suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_specific_properties(payer_account_currency_fph)

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

    subject_line = "Payment received from " + payer_account_owner_hrns

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
            "",         # subject prefix string
            subject_line,               # subject
            "",                         # stewardship_id (n/a)
            0,                          # longevity (indefinite)
            "",                         # expiry_datetime (no expiry)
            payer_account_fph,      # string
            payee_account_fph,      # string
            amount,                 # integer
            message_body,               #
            False                       # indelibility
        )
#    if m:
#        print("Problem in  send_message( )  function")
#        print(m)

    return ""

#==============================================================================








def make_om_payment(
        payer_account_holder_hrns,
        payee_account_holder_hrns,
        currency_hrns,
        amount,
        annotation
    ):


    return status, m
