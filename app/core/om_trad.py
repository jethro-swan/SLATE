#!/home/slate/SLATE/venv/bin/python3

# This file contains functions to emulate the "traditional" OM mode pairing a
# re-useable *ahid* identifier with a *currency* identifier.
#
# On the surface, the bahaviour is a little different from that of the
# SLATE/NESTS approach in that the *account* created to represent the pairing
# is only ever identified (to most users in "om_trad" mode) indirectly by
# *ahid* and *currency*.

# The ahid_hrns and currency_hrns are entered in a form.
# These are used to create a new pairing which maps to a new *account*.

# The *ahid* HRNS can be retrieved by FPH in the same way as any
# other entity type.

# Each *primid* maintains a map of *pairings* as a dictionary of lists:
#
#   ahid_hrns: [currency1_fph, currency2_fph, ...]
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
from app.core.slate_core import account_status
from app.core.slate_core import new_namespace
from app.core.slate_core import new_primid
from app.core.slate_core import new_currency
from app.core.slate_core import identify_entity
from app.core.slate_core import split_hrns
from app.core.slate_core import get_currency_specific_properties

from app.core.common import ledger_timestamp

from app.core.messaging import send_message

from app.core.regexp_list import re_pvalue

from app.core.constants import ENTITIES_DB
from app.core.constants import PAYMENTS_DB

#=============================================================================

##def split_hrns(identifier_hrns):
##    if not re_hrns.match(identifier_hrns):
##        return "", ""
##    names = identifier_hrns.split(".")
##    name = names.pop(0)
##    parent_namespace_hrns = ".".join(names)
##    return name, parent_namespace_hrns


#=============================================================================

def retrieve_pmap(owner_identifier):

    owner_fph, \
    owner_hrns, \
    owner_type, \
    m = identify_entity(owner_identifier)
    if (owner_type != "primid"):
        return {}, owner_identifier + " is not a primid"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT pmap FROM primids WHERE entity_fph = ?",
            (owner_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
        # If no pmap exists yet, it is created:
        if result is None:
#            cursor.execute(
#                "UPDATE primids SET pmap = ? WHERE entity_fph = ?",
#                (owner_fph, pickle.dumps({}))
#            )
#            conn.commit()
            #cursor.close()
            return None, ""
#            return {}, ""
        elif isinstance(result, tuple) and (result[0] is None):
            return None, ""
        else:
            pmap = pickle.loads(result[0])
            #cursor.close()

#        print()
#        print("Retrieved test pmap:")
#        print(pmap)
#        print()


        return pmap, ""     # dictionary of  ahid_hrns:currency_hrns
                            # pairs for display in table.


#=============================================================================

def create_new_pairing(
        owner_identifier,   # HRNS or FPH
        ahid_hrns,          # HRNS
        currency_hrns       # HRNS
    ):

    # The *currency* and owner *primid* are validated before proceeding to
    # create a new *account-holder*. Only if both exist will a new *account*
    # or *account-holder* be created.

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_hrns)
    if (etype != "currency"):
        #print(currency_hrns + " is not a currency")
        return "", currency_fph + " is not a currency"

    owner_fph, \
    owner_hrns, \
    owner_type, \
    m = identify_entity(owner_identifier)
    if (owner_type != "primid"):
        return "", owner_identifier + " is not a primid"

    # If the *ahid* does not exist already it must be created:
    #
    ahid_fph, \
    do_not_overwrite_original_ahid_hrns, \
    etype, \
    m = identify_entity(ahid_hrns)

    #print(">>> " + ahid_hrns + ":" + currency_hrns)




    if ahid_fph == "": # does not exist

        ahid_name, parent_hrns = split_hrns(ahid_hrns)

        parent_namespace_fph, \
        parent_namespace_hrns, \
        etype, \
        m = identify_entity(parent_hrns)

        if not re_hrns.match(parent_namespace_hrns):
            return "", "Invalid parent namespace: " + parent_namespace_hrns

        # The *ahid* is added to the HRNS>FPH and FPH>HRNS maps:
        #
        ahid_fph, m = hrns_to_fph(ahid_hrns)

        # The *ahid* is then added to the entities_common table.
        # (Unlike other entity types, *ahid* has no table for
        # specific properties.)
        #
        add_entity_common_properties(
            ahid_fph,
            parent_namespace_fph,
            "ahid",
            "",         # n/a
            False,      # not applicable to *pairing*
            owner_fph,
            True
        )

    # At this point, whether or not it has been necessary to create it, we now
    # have both the HRNS and the FPH of the *ahid*. It can now be paired with
    # the specified *currency* to index a new *account*.

    # The *account* created for this *account-holder"|*currency* pairing will
    # not usually be seen by its owner, but it still needs an HRNS - both in
    # order to be able to assign it an FPH and to insure that it is both unique
    # and easily related to the two components of the pairing. Therefore its
    # name is constructed from the two paired HRNS:
    #
    ah_id = "^".join(ahid_hrns.split("."))
    c_id = "^".join(currency_hrns.split("."))
    account_name = "_".join(["", ah_id, "&", c_id, ""])
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

    # The *ahid* may be paired with any *currency* (once only). These
    # serve as the co-ordinates in a grid identifying the *account* created
    # above.
    #
    # If a *pairing* entity does not exist already it is created.
    #
    # The pairings dictionary is retrieved:
    pmap, m = retrieve_pmap(owner_identifier)

    if pmap is None:
        pmap = {}

    if not (ahid_hrns in pmap):
        pmap[ahid_hrns] = {}

    pmap[ahid_hrns][currency_hrns] = account_fph

    for ahid_hrns in pmap.keys():
        print(ahid_hrns)
        for c_hrns in pmap[ahid_hrns].keys():
            print(ahid_hrns + " : " + c_hrns + " > " + pmap[ahid_hrns][c_hrns])


    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE primids SET pmap = ? WHERE entity_fph = ?",
            (pickle.dumps(pmap), owner_fph)
        )
        conn.commit()
        cursor.close()

#    print()
#    print("pairing created between " + ahid_hrns + " and " + currency_hrns)
#    print("for " + owner_identifier)
#    print("mapping to account " + account_fph)
#    print()

    return account_fph

#=============================================================================




#=============================================================================

def get_ahid_primid(ahid_hrns):

    ahid_fph, \
    do_not_overwrite_original_ahid_hrns, \
    etype, \
    m = identify_entity(ahid_hrns)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT entity_type, owner_fph, active
            FROM entities_common
            WHERE entity_fph = ?
            """,
            (ahid_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if (result is None) or (result[0] != "ahid") or (not result[2]):
        return ""
    else:
#        print("result[1] = ", end="")
#        print(result[1])
        return result[1] # owner primid FPH

#=============================================================================

def list_primid_ahids(primid_fph):





    return ahids_list





#=============================================================================

def retrieve_pairing_account_fph(ahid_hrns, currency_identifier):

    if not re_hrns.match(ahid_hrns):
        return "", "", ahid_hrns + " is not an account-holder"

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_identifier)
    if (etype != "currency"):
        return "", "", currency_fph + " is not a currency"

    primid_fph = get_ahid_primid(ahid_hrns)
    if primid_fph:
        #pmap = get_ahid_pmap(primid_fph)
        pmap, m = retrieve_pmap(primid_fph)
    else:
        return "", "", "Unable to retrieve pmap for ahid " + ahid_hrns

#    print()
#    print("pmap = ", end="")
#    print(pmap)
#    print()
#    print("pmap.keys() = ", end="")
#    print(pmap.keys())
#    print()
    if not (ahid_hrns in pmap.keys()):
        return "", "", ahid_hrns + " is not an account-holder"

    if not (currency_hrns in pmap[ahid_hrns].keys()):
        return "", "", ahid_hrns + " does not use currency " + currency_hrns

    account_fph = pmap[ahid_hrns][currency_hrns]

    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(account_fph)
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
        payer_ahid_hrns,
        payee_ahid_hrns,
        currency_hrns,
        amount,
        annotation
    ):

    payer_account_fph, \
    payer_primid_fph, \
    m = retrieve_pairing_account_fph(payer_ahid_hrns, currency_hrns)
    if m:
        return "", "", m

    payee_account_fph, \
    payee_primid_fph, \
    m = retrieve_pairing_account_fph(payee_ahid_hrns, currency_hrns)
    if m:
        return "", "", m

    payer_account_exists, \
    payer_account_active, \
    payer_account_currency_fph, \
    payer_account_owner_fph, \
    payer_account_ahid_fph, \
    payer_account_balance, \
    payer_volume, \
    m = account_status(payer_account_fph)
    if not payer_account_exists:
        return "", "", "Payer account " + payer_account_fph + " does not exist"
    if not payer_account_active:
        return "", "", "Payer account " + payer_account_fph + " is inactive"

    payee_account_exists, \
    payee_account_active, \
    payee_account_currency_fph, \
    payee_account_owner_fph, \
    payee_account_ahid_fph, \
    payee_account_balance, \
    payee_volume, \
    m = account_status(payee_account_fph)
    if not payee_account_exists:
        return "", "", "Payee account " + payee_account_fph + " does not exist"
    if not payee_account_active:
        return "", "", "Payee account " + payee_account_fph + " is inactive"

    if not re_pvalue.match(str(amount)):
        return str(amount) + " is not a valid payment"

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
    m = get_currency_specific_properties(currency_hrns)

    #--------------------------------------------------------------------------
    # Then the payment is recorded in the journal:

    payer_ahid_fph, m = hrns_to_fph(payer_ahid_hrns)
    payee_ahid_fph, m = hrns_to_fph(payee_ahid_hrns)



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

    subject_line = "Payment received from " + payer_ahid_hrns

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
            "",                 # payer_account_fph unused in this mode
            "",                 # payee_account_fph unused in this mode
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








def make_om_payment(
        payer_ahid_hrns,
        payee_ahid_hrns,
        currency_hrns,
        amount,
        annotation
    ):


    return status, m


#==============================================================================
# CSV import
#
# This is a little different from the CSV import system used for
# *account*-to-*account* payments.
# (1) It works only with the UTF-8 Latin character set
# (2) It supports the automatic completion of incomplete namespace chains
# (3) It allows for the import of mixed entity types using a single CSV file
#
# The input format is:
#
#   | *currency* | payer *ahid* | payee *ahid* | amount | annotation |
#   | HRNS       | HRNS         | HRNS         |        |            |
#

def complete_parent_namespace_chain(identifier_hrns):
    s_fph, m = hrns_to_fph("adm.cc")
    c_fph, m = hrns_to_fph("cc")
    entity_fph, entity_hrns, etype, m = identify_entity(identifier_hrns)
    if entity_fph: # the entity exists already
        return entity_fph, entity_hrns, identifier_hrns + " exist already"
    if not re_hrns.match(identifier_hrns):
        return "", "", identifier_hrns + " is invalid HRNS"
    parent_namespace_chain_incomplete = True
    chain_links = []
    parent_hrns_ = identifier_hrns
    parent_ns_fph = ""
    while not parent_ns_fph:
        parent_ns_fph, parent_ns_hrns, etype, m = identify_entity(parent_hrns_)
        name, parent_hrns = split_hrns(parent_hrns_)
        chain_links.append(name)
        parent_hrns_ = parent_hrns
    ns_fph = parent_ns_fph
    chain_links.pop()
    while len(chain_links) > 0:
        ns_name = chain_links.pop()
        ns_fph, ns_hrns, m = new_namespace(ns_name, ns_fph, c_fph, s_fph)
    return ns_fph

def create_import_primid(primid_hrns):
    if not re_hrns.match(primid_hrns):
        return "", "", primid_hrns + " is invalid HRNS"
    primid_fph, primid_hrns, etype, m = identify_entity(primid_hrns)
    if primid_fph: # the entity exists already
        return primid_fph, primid_hrns, primid_hrns + " exist already"
    name, parent_hrns = split_hrns(primid_hrns)
    parent_fph = complete_parent_namespace_chain(parent_hrns)
    primid_fph, primid_hrns, access_token,
    m = new_primid(
            username,
            parent_namespace_fph,
            realname,
            email_address_1,
            email_address_2,
            password,
            pin
        )

def create_import_currency(currency_hrns):
    if not re_hrns.match(currency_hrns):
        return "", "", currency_hrns + " is invalid HRNS"
    s_fph, m = hrns_to_fph("adm.cc")
    currency_fph, currency_hrns, etype, m = identify_entity(currency_hrns)
    if currency_fph: # the entity exists already
        return currency_fph, currency_hrns, currency_hrns + " exist already"
    name, parent_hrns = split_hrns(currency_hrns)
    parent_fph = complete_parent_namespace_chain(parent_hrns)
    print(parent_fph)
    c_fph, c_hrns, m = new_currency(name, parent_fph, s_fph, "", "", name)
    return c_fph, c_hrns, m
