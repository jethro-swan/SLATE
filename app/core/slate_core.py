import sqlite3
import random
import os
import pickle
from pathlib import Path
from string import ascii_lowercase

#from flask_bcrypt import Bcrypt # 2024-11-10: Try this out to resolve problem
                                # with check_auth_hash( )
                                # ("ValueError: Invalid salt")

from .constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
from .constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from .constants import SUBSTRATE_FPH
from .common import filename_timestamp as timestamp
from .common import nshash
from .fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from .fph_hrns_maps import delete_fph_from_map
from .dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from .dbm_functions import dbm_create_map
from .auth import auth_hash, generate_access_token
from .regexp_list import *
from .unix_functions import fcopy
from .cctld_list import *

#from app import bcrypt  # added 2024-11-10

#------------------------------------------------------------------------------
# In NESTS the FPH has so far been formed as the hash of the FIP, but making it
# the hash of the HRNS instead will simplify compatibility between SLATE and
# NESTS and speed up the HRNS to FPH mapping without having any signifcant
# impact on the FPH to HRNS and FPH to FIP mappings.

#==============================================================================
## Create the SQLite entities database:

def create_entities_db():

    if os.path.exists(ENTITIES_DB):
        # If the database exists already, it is deleted after a time-stamped
        # copy has been saved.
        fcopy(ENTITIES_DB, DB_BKP_DIR + '/entities_' + timestamp() + '.db')
        os.remove(ENTITIES_DB)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # A table is created for the entities' common properties:
        cursor.execute(
            """
    	    CREATE TABLE IF NOT EXISTS entities_common (
                entity_fph TEXT PRIMARY KEY,
                parent_namespace_fph TEXT,
                entity_type TEXT,
                active INTEGER NOT NULL
            );
            """
        )
        # Create namespaces table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS namespaces (
                entity_fph TEXT PRIMARY KEY,
                stewards_fph_list BLOB
            );
            """
        )
        # Create primids table:
#        cursor.execute(
#            """
#    	    CREATE TABLE IF NOT EXISTS primids (
#                entity_fph TEXT PRIMARY KEY,
#                primid_realname TEXT,
#                primid_email_1 TEXT NOT NULL,
#                primid_email_2 TEXT,
#                secids_fph_list BLOB,
#                accounts_fph_list BLOB,
#                stewardships_fph_list BLOB,
#                password_hash TEXT NOT NULL,
#                pin TEXT,
#                access_token_hash TEXT
#            );
#            """
#        )
        # Create primids table:
        cursor.execute(
            """
    	    CREATE TABLE IF NOT EXISTS primids (
                entity_fph TEXT PRIMARY KEY,
                primid_realname TEXT,
                primid_email_1 TEXT NOT NULL,
                primid_email_2 TEXT,
                secids_fph_list BLOB,
                accounts_fph_list BLOB,
                stewardships_fph_list BLOB,
                password_hash BLOB NOT NULL,
                pin TEXT,
                access_token_hash BLOB
            );
            """
        )
        # Create secids table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS secids (
                entity_fph TEXT,
                primid_fph TEXT,
                accounts_fph_list BLOB
            );
            """
        )
        # Create currencies table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS currencies (
                entity_fph TEXT PRIMARY KEY,
                currency_prefix TEXT,
                currency_suffix TEXT,
                stewards_fph_list BLOB
            );
            """
        )
        # Create accounts table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                entity_fph TEXT PRIMARY KEY,
                account_owner_fph TEXT NOT NULL,
                account_currency_fph TEXT NOT NULL,
                account_balance INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        # Create currency_accounts table:  ### PROBABLY NOT NEEDED
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS currency_accounts (
                currency_fph TEXT,
                account_fph TEXT
            );
            """
        )
        # Create login (temporary data) table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS login (
                entity_fph TEXT,
                login_id_fph TEXT,
                login_authenticated INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        conn.commit()
        cursor.close()

#==============================================================================
## The entities' common properties are recorded:
#
# The *namespaces", *currencies*, "primids", *secids* and *accounts* all have
# some properties in common, so these are held in a seprate table from those
# used to hold the properties distinct to each entity type.

# Record the common properties at the point of an entity's creation:
def add_entity_common_properties(
        entity_fph,
        parent_namespace_fph,
        entity_type,
        active
    ):
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO entities_common (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                active
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                active
            )
        )
        conn.commit()
        cursor.close()
    return

#==============================================================================
## Get the common properties for this entity identified by FPH or HRNS.
#
# Returns an error message in the event of any problem.

def get_entity_common_properties(entity_id): # FPH or HRNS

    entity_fph, entity_hrns, entity_type, m = identify_entity(entity_id)
    if m:
        return "", "", "", False, m

    #if not re_fph.match(entity_fph):
    #    return entity_fph, "", False, entity + " is not an FPH"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT parent_namespace_fph, active
            FROM entities_common
            WHERE entity_fph = ?
            """,
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is not None:
        parent_namespace_fph = result[0]
        active = result[1]
        return entity_fph, parent_namespace_fph, entity_type, active, ""
    else:
        return entity_fph, "", "", False, "Entity " + entity_fph + "not found"

#==============================================================================
## Check whether an entity is currently active:

def entity_is_active(entity_id):

    entity_fph, entity_hrns, entity_type, m = identify_entity(entity_id)
    if m:
        return False, m

    entity_fph, \
    parent_namespace_fph, \
    entity_type, \
    active, \
    m = get_entity_common_properties(entity_id)
    return active, m

#==============================================================================
## Get the entity's type:

def get_entity_type(entity_fph):

    if not re_fph.match(entity_fph):
        return "", entity_fph + " is not an FPH"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT entity_type
            FROM entities_common
            WHERE entity_fph = ?
            """,
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            entity_type = result[0]
            if entity_type in [
                                "namespace",
                                "currency",
                                "primid",
                                "secid",
                                "account"
                              ]:
                return entity_type, ""
        return "", "Type cannot be identified for " + entity_fph

#==============================================================================
#
#
# MOVE THIS

# NB, this is useful only when an account is created and added to an agent
#     (*primid* or *secid*) so should be moved to become a sub-function of
#     new_account().

def add_account_to_currency(account_fph, currency_fph):
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO currency_accounts (currency_fph, account_fph)
            VALUES (?, ?)
            """,
            (currency_fph, account_fph)
        )
        conn.commit()
        cursor.close()

    return


#==============================================================================
## Update the *primid* contact details:

def update_primid_contact_details(
        primid_fph,
        primid_realname,
        primid_email_1,
        primid_email_2
    ):
    errors = ""
    if not re_match(primid_fph):
        errors += primid_fph + " is not an FPH"
        return errors
    etype, m = get_entity_type(primid_fph)
    if m:
        errors += m + "\n"
    if  etype != "primid":
        errors += primid_fph + " is not a primid"
        return errors
    update_needed = False
    update_str = "UPDATE primids SET "
    values_str = "("
    if primid_realname and re_realname.match(primid_realname):
        update_str += "primid_realname = ?, "
        values_str += primid_realname + ", "
        update_needed = True
    else:
        errors += primid_realname + " is not a valid name"
    if primid_email_1 and re_email.match(primid_email_1):
        update_str += "primid_email_1 = ?, "
        values_str += primid_email_1 + ", "
        update_needed = True
    else:
        errors += primid_email_1 + " is not a valid email address"
    if primid_email_2 and re_email.match(primid_email_2):
        update_str += "primid_email_2 = ?, "
        values_str += primid_email_2 + ", "
        update_needed = True
    else:
        errors += primid_email_2 + " is not a valid email address"
    # If none of the values provided are valid, there is no need to update the
    # database.
    if update_needed:
        update_str += "WHERE entity_fph = ?"
        update_str = update_str.replace(", WHERE", " WHERE")
        values_str += ")"
        values_str = values_str.replace(",)", ")") # remove the final comma
        with sqlite3.connect(ENTITIES_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(update_str, values_str)
            conn.commit()
            cursor.close()
    return errors

#==============================================================================
## Update the *primid* access details:

def update_primid_access_details(
        primid_fph,
        password,
        pin,
        access_token
    ):
    errors = ""
    if not re_match(primid_fph):
        errors += primid_fph + " is not an FPH\n"
        return errors
    etype, m = get_entity_type(primid_fph)
    if m:
        errors += m + "\n"
    if etype != "primid":
        errors += primid_fph + " is not a primid\n"
        return errors
    update_needed = False
    update_str = "UPDATE primids SET "
    values_str = "("
    if password:
        password_hash = auth_hash(password)
        update_str += "password_hash = ?, "
        values_str += password_hash + ", "
        update_needed = True
    else:
        errors += password + " is not a valid password"
    if pin and re_pin.match(pin):
        update_str += "pin = ?, "
        values_str += pin + ", "
        update_needed = True
    if access_token and re_access_token.match(access_token):
        access_token_hash = auth_hash(access_token)
        update_str += "access_token_hash = ?, "
        values_str += access_token_hash + ", "
        update_needed = True
    update_str += "WHERE entity_fph = ?"
    update_str = update_str.replace(", WHERE", " WHERE")
    values_str += ")"
    values_str = values_str.replace(", )", ")") # remove the final comma
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(update_str, values_str)
        conn.commit()
        cursor.close()
    return errors

#==============================================================================
## Retrieve the *primid* access details:

def retrieve_primid_access_details(primid_identifier):

    primid_fph, \
    primid_hrns, \
    etype, \
    m = identify_entity(primid_identifier)
    if m:
        return "", "", "", m

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT password_hash, pin, access_token_hash
            FROM primids
            WHERE entity_fph = ?
            """,
            (primid_fph,)
        )
        result = cursor.fetchone()
        if result is not None:
            password_hash = result[0]
            pin = result[1]
            access_token_hash = result[2]
            return password_hash, pin, access_token_hash, ""
        else:
            "", "", "", primid_identifier + " authentication data unavailable"

#==============================================================================
## Retrive the status of an account:
#
# returns:  exists          (boolean),
#           active          (boolean),
#           currency        (FPH),
#           owner           (FPH),
#           errors          text
#
def account_status(account_fph):
    if not re_fph.match(account_fph):
        return "", "", 0, "Invalid FPH: " + account_fph

    #account_fph = "'" + account_fph + "'"
    # wrapped to enable SQLite to accept it.

    entity_fph, \
    parent_namespace_fph, \
    entity_type, \
    active, \
    m = get_entity_common_properties(account_fph)
    if m:
        return False, False, "", "", 0, m
    if entity_type != "account":
        return False, False, "", "", 0, account_fph + " is not an account"

    currency_fph, \
    owner_fph, \
    balance, \
    m = get_account_specific_properties(account_fph)
    if m:
        return False, False, "", "", 0, m

    return True, active, currency_fph, owner_fph, balance, ""

#==============================================================================

def namespace_status(namespace_fph):

    if not re_fph.match(namespace_fph):
        return "", "", [], "Invalid FPH: " + namespace_fph

    entity_fph, \
    parent_namespace_fph, \
    entity_type, \
    active, \
    m = get_entity_common_properties(namespace_fph)
    if m:
        return False, False, [], m
    if entity_type != "namespace":
        return False, False, [], namespace_fph + " is not a namespace"

    stewards_list, m = list_stewards(namespace_fph)
    if m:
        return False, False, [], m

    return True, active, stewards_list, ""

#==============================================================================
# A new *primid* is created in the specified namespace. This function is used
# only at the point of registration.

def new_primid(
        username,
        parent_namespace_fph,
        realname,
        email_address_1,
        email_address_2,
#        password_already_hashed,
        password,
        pin
    ):

    #if not re_fph.match(parent_namespace_fph):
    #    return "", "", "", "Invalid parent namespace: " + parent_namespace_fph
    errors = ""

    #if re_password.match(password):
    #    password_hash = auth_hash(password)
#    password_hash = auth_hash(password) # restored 2024-11-10 19.50
    #else:
    #    return "", "", "", "Invalid password provided."

    if not re_pin.match(pin):
        return "", "", "", "Invalid PIN provided."

    etype, m = get_entity_type(parent_namespace_fph)
    if m:
        return "", "", "", m # parent_namespace_fph is invalid
    if etype != "namespace":
        return "", "", "", parent_namespace_fph + " is not a namespace"
    namespace_hrns = fph_to_hrns(parent_namespace_fph)
    primid_hrns = username + "." + namespace_hrns

    if fph_to_hrns(nshash(primid_hrns)):
        return "", "", "", primid_hrns + "  already registered in FPH>HRNS map"

    primid_fph, m = hrns_to_fph(primid_hrns)
    if m:
        delete_fph_from_map(primid_fph)
        return "", "", "", m

    if not re_realname.match(realname):
        errors += "Invalid real name \"" + realname + "\" discarded " \
               + "so the primid has been created without a real name.\n"
        primid_realname = ""

    # The *primid* cannot be created if no valid primary email address has been
    # provided:
    if not email_address_1:
        delete_fph_from_map(primid_fph)
        return "", "", "", "No email address provided"
    if not re_email.match(email_address_1):
        delete_fph_from_map(primid_fph)
        return "", "", "", "Invalid entry: primary email address"

    # If an invalid secondary email address has been provided it is discarded
    # and the *primid* is created with only a primary email address:
    if email_address_2:
        if not re_email.match(email_address_2):
            errors += "Invalid email address " + email_address_2 \
                   + " has been discarded.\n"
            email_address_2 = ""

    #accounts_fph_blob = pickle.dumps([])

    # The access authentication details are now added:

    #stewardships_fph_list = pickle.dumps([])
    secids_fph_list = []
    accounts_fph_list = []
    stewardships_fph_list = []

    access_token = generate_access_token()
    access_token_hash = auth_hash(access_token)

    add_entity_common_properties(
        primid_fph,
        parent_namespace_fph,
        "primid",
        True
    )

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO primids (
                entity_fph,
                primid_realname,
                primid_email_1,
                primid_email_2,
                secids_fph_list,
                accounts_fph_list,
                stewardships_fph_list,
                password_hash,
                pin,
                access_token_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                primid_fph,
                realname,
                email_address_1,
                email_address_2,
                pickle.dumps(secids_fph_list),          # empty list
                pickle.dumps(accounts_fph_list),        # empty list
                pickle.dumps(stewardships_fph_list),    # empty list
                #password_already_hashed,    # restored 2024-11-10 19.50
                auth_hash(password),        # restored 2024-11-10 19.50
                pin,
                auth_hash(access_token),
            )
        )
        conn.commit()
        cursor.close()

    return primid_fph, primid_hrns, access_token, m

# Although the initial access token is generated automatically here, it may be
# updated by the primid at any time.

#==============================================================================
## A new *secid* is created:

def new_secid(
        username,
        parent_namespace_fph,
        primid_fph
    ):
    if not re_fph.match(parent_namespace_fph):
        return "", "", "Invalid parent namespace: " + parent_namespace_fph

    parent_namespace_hrns = fph_to_hrns(parent_namespace_fph)
    secid_hrns = username + "." + parent_namespace_hrns
    if fph_to_hrns(nshash(secid_hrns)):
        return "", "", secid_hrns + "  already registered in FPH>HRNS map"
    else:
        secid_fph, m = hrns_to_fph(secid_hrns)
        if m:
            return "", "", m

    add_entity_common_properties(
        secid_fph,
        parent_namespace_fph,
        "secid",
        True
    )
    # Add the *secid*-specific properties:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO secids (
                entity_fph,
                primid_fph,
                accounts_fph_list
            )
            VALUES (?, ?, ?)
            """,
            (
                secid_fph,
                primid_fph,         # The *primid* (owner) of this *secid*
                pickle.dumps([])    # Empty list: accounts will be added later.
            )
        )
        conn.commit()
        cursor.close()

    return secid_fph, secid_hrns, ""

#==============================================================================
## A new namespace is created:

def new_namespace(
        namespace_name,
        parent_namespace_fph,
        initial_steward_fph
    ):

    if not re_fph.match(parent_namespace_fph):
        return "", "", "Invalid parent namespace FPH: " + parent_namespace_fph

    if not re_fph.match(initial_steward_fph):
        return "", "", "Invalid initial steward FPH: " + initial_steward_fph

    parent_namespace_hrns = fph_to_hrns(parent_namespace_fph)
    if parent_namespace_hrns:
        namespace_hrns = namespace_name + "." + parent_namespace_hrns
    else:
        namespace_hrns = namespace_name

    if fph_to_hrns(nshash(namespace_hrns)):
        return "", "", namespace_hrns + "  already registered in FPH>HRNS map"

    namespace_fph, m = hrns_to_fph(namespace_hrns)

    #stewards_fph_blob = pickle.dumps(list([initial_steward_fph]))

    add_entity_common_properties(
        namespace_fph,
        parent_namespace_fph,
        "namespace",
        True
    )

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO namespaces (entity_fph, stewards_fph_list)
            VALUES (?, ?)
            """,
            (namespace_fph, pickle.dumps([initial_steward_fph]))
        )
        conn.commit()
        cursor.close()

    return namespace_fph, namespace_hrns, ""

#==============================================================================
## A new currency is added:

def new_currency(
        currency_name,
        parent_namespace_fph,
        initial_steward_fph,
        currency_prefix,
        currency_suffix
    ):
    # The initial account in this currency is assigned to its initial steward
    # (which must exist already).

    if not re_fph.match(parent_namespace_fph):
        return "", "", "Invalid parent namespace FPH: " + parent_namespace_fph

    if not re_fph.match(initial_steward_fph):
        return "", "", "Invalid initial steward FPH: " + initial_steward_fph

    parent_namespace_hrns = fph_to_hrns(parent_namespace_fph)
    currency_hrns = currency_name + "." + parent_namespace_hrns

    if fph_to_hrns(nshash(currency_hrns)):
        return "", "", currency_hrns + "  already registered in FPH>HRNS map"

    currency_fph, m = hrns_to_fph(currency_hrns)

    initial_steward_hrns = fph_to_hrns(initial_steward_fph)

    add_entity_common_properties(
        currency_fph,
        parent_namespace_fph,
        "currency",             # entity type
        True                    # active flag
    )

    # Now add currency specific properties:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO currencies (
                entity_fph,
                currency_prefix,
                currency_suffix,
                stewards_fph_list
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                currency_fph,
                currency_prefix,
                currency_suffix,
                pickle.dumps([])
                #pickle.dumps([initial_steward_fph])
            )
        )
        conn.commit()
        cursor.close()

    return currency_fph, currency_hrns, ""

#==============================================================================
## A new account is created in a specified currency:

def new_account(
        account_hrns,
        agent_fph,      # (Agent may be a *primid* or a *secid*)
        currency_fph
    ):

    if not re_hrns.match(account_hrns):
        return "", "", "Invalid account HRNS: " + account_hrns

    agent_fph, \
    agent_hrns, \
    agent_type, \
    m = identify_entity(agent_fph)

    if agent_type == "primid":
        a_table = "primids"
    elif agent_type == "secid":
        a_table = "secids"
    else:
        return "", "", agent_fph + " is not an agent"

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_fph)
    if (etype != "currency"):
        return "", "", currency_fph + " is not a currency"

    if fph_to_hrns(nshash(account_hrns)):
        return "", "", account_hrns + "  already registered in FPH>HRNS map"

    account_fph, m = hrns_to_fph(account_hrns)

    add_entity_common_properties(
        account_fph,
        agent_fph,
        "account",
        True
    )

    # Now add account specific properties:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO accounts (
                entity_fph,
                account_owner_fph,
                account_currency_fph,
                account_balance
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                account_fph,
                agent_fph,      # Owner may be either *primid* or *secid"
                currency_fph,
                0
            )
        )
        conn.commit()

        select_string = "SELECT accounts_fph_list" \
                      + " FROM " + a_table \
                      + " WHERE entity_fph = ?"
        update_string = "UPDATE " + a_table \
                      + " SET accounts_fph_list = ?" \
                      + " WHERE entity_fph = ?"
    #with sqlite3.connect(ENTITIES_DB) as conn:
    #    cursor = conn.cursor()
        cursor.execute(select_string, (agent_fph,))
        result = cursor.fetchone()
        accounts_fph_blob = result[0]
        accounts_fph_list = pickle.loads(accounts_fph_blob)
        accounts_fph_list.append(account_fph)
        accounts_fph_blob = pickle.dumps(accounts_fph_list)
        cursor.execute(update_string, (accounts_fph_blob, agent_fph))



        conn.commit()

        cursor.close()

    #add_account_to_currency(
    #    account_fph,
    #    currency_fph
    #)

    if m:
        return "", "", m
    else:
        return account_fph, account_hrns, ""

#==============================================================================
##

def get_currency_specific_properties(currency_identifier):

    currency_fph, \
    currency_hrns, \
    entity_type, \
    m = identify_entity(currency_identifier)
    if m:
        return "", "", "", "", "", m

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Add the stewarded entity's FPH to the *primid*'s stewardships list:
        cursor.execute(
            """
            SELECT currency_prefix, currency_suffix, stewards_fph_list
            FROM currencies
            WHERE entity_fph = ?
            """,
            (currency_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        m = "Currency " + fph_to_hrns(currency_fph) + " not found"
        return "", "", "", "", "", m
    else:
        prefix = result[0]
        suffix = result[1]
        stewards_fph_blob = result[2]
        stewards_fph_list = pickle.loads(stewards_fph_blob)

        return currency_fph, currency_hrns, prefix, suffix, stewards_list, ""




def get_currency_name(currency_fph):
    hrns = fph_to_hrns(currency_fph)
    if hrns == "":
        return ""
    else:
        hrnsa = hrns.split(".")
        return hrnsa[0]

#==============================================================================
## List the *primid*'s accounts: KEEP

def list_primid_accounts(primid_fph):

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT accounts_fph_list
            FROM primids
            WHERE entity_fph = ?
            """,
            (primid_fph,)
        )
        result = cursor.fetchone()
        #cursor.close()
        #print("results = ", end="")
        #print(results)
    if result is None:
        accounts_fph_list = []
        accounts_fph_blob = pickle.dumps(accounts_fph_list)
        cursor.execute(
            """
            UPDATE primids
            SET accounts_fph_list = ?
            WHERE entity_fph = ?
            """,
            (accounts_fph_blob, primid_fph)
        )
        conn.commit()
        cursor.close()
        return [], "Primid " + fph_to_hrns(primid_fph) + " has no accounts."
    else:
        cursor.close()
        accounts_fph_blob = result[0]
        accounts_fph_list = pickle.loads(accounts_fph_blob)
        return accounts_fph_list, ""    # list + message

#==============================================================================
## List the *secid*'s accounts: #

def list_secid_accounts(secid_fph):
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT accounts_fph_list
            FROM secids
            WHERE entity_fph = ?
            """,
            (secid_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        accounts_fph_list = []
        accounts_fph_blob = pickle.dumps(accounts_fph_list)
        cursor.execute(
            """
            UPDATE secids
            SET accounts_fph_list = ?
            WHERE entity_fph = ?
            """,
            (accounts_fph_blob, secid_fph)
        )
        conn.commit()
        cursor.close()
        return [], "The secid " + secid_fph + " has no accounts."
    else:
        accounts_fph_blob = result[0]
        accounts_fph_list = pickle.loads(accounts_fph_blob)
        return accounts_fph_list, ""    # list + message

#==============================================================================
##
#
# NB  The two functions above may be combined into a single function:

def list_agent_accounts(agent_fph):

    etype, m = get_entity_type(agent_fph)
    if m:
        return [], m
    if etype == "primid":
        table = " primids "
    elif etype == "secid":
        table = " secids "
    else:
        return [], agent_fph + " is neither primid nor secid but " + etype

    sstr = "SELECT accounts_fph_list FROM" + table + "WHERE entity_fph = ?"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(sstr, (agent_fph,))
        result = cursor.fetchone()
        if result is None:
            accounts_fph_list = []
        else:
            accounts_fph_blob = result[0]
            accounts_fph_list = pickle.loads(accounts_fph_blob)
            conn.commit()
        cursor.close()

    return accounts_fph_list, ""    # list + message


#==============================================================================
## Get the currency of an account: KEEP

def get_account_currency(account_fph):
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT account_currency_fph
            FROM accounts
            WHERE entity_fph = ?
            """,
            (account_fph,)
        )
        currency_fph = cursor.fetchone()[0]
        cursor.close()
    return currency_fph

#==============================================================================
# Identify the account in the specified currency:
#
# A currency will usually have a large number of accounts, so these are stored
# in a separate table rather than in a pickled blob in the currencies table.

def list_accounts_in_currency(currency_identifier):

    currency_fph, \
    currency_hrns, \
    entity_type, \
    m = identify_entity(currency_identifier)
    if (entity_type != "currency"):
        return [], currency_identifier + " is not a currency.\n"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT entity_fph
            FROM accounts
            WHERE account_currency_fph = ?
            """,
            (currency_fph,)
        )
        result_list = cursor.fetchall()
        cursor.close()

    if result_list is None:
        return [], "Currency " + currency_identifier + " has no accounts.\n"

    accounts_fph_list = []
    for account_fph in result_list:
        accounts_fph_list.append("".join(account_fph).strip())
        # FIX: The results retrieved are currently typles where they should be
        # strings.
        #print(account_fph)

    return accounts_fph_list, ""    # list + message

#==============================================================================
# Identify the account (if any) in which the primid has access to the specified
# currency: KEEP

def list_primid_accounts_in_currency(primid_identifier, currency_identifier):

    primid_fph, \
    primid_hrns, \
    etype, \
    m = identify_entity(primid_identifier)
    if etype != "primid":
        return [], primid_identifier + " is not a primid.\n"

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(primid_identifier)
    if etype != "currency":
        return [], currency_identifier + " is not a currency.\n"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT entity_fph FROM accounts
            WHERE account_currency_fph = ?, account_owner_fph ?
            """,
            (currency_fph,primid_fph)
        )
        result_list = cursor.fetchall()
        cursor.close()

    if result_list is None:
        return [], "No results found.\n"
    accounts_fph_list = []
    for account_fph in result_list:
        accounts_fph_list.append(account_fph)

    return accounts_fph_list, ""

#==============================================================================
## List the *primid*'s *account*s' *currencies*: KEEP
#
# For a specified *primid*, return a list the *currencies* in which it has an
# *account*

def list_primid_currencies(primid_fph): # in which an primid has accounts
    accounts_fph_list, m = list_primid_accounts(primid_fph)
    currencies_fph_list = []
    for account_fph in accounts_fph_list:
        currencies_fph_list.append(get_account_currency(account_fph))
    return currencies_fph_list    # list


#==============================================================================
## List the *secid*'s *account*s' *currencies*: KEEP
#
# For specified *secid*, return a list the *currencies* in which it has an
# *account*

def list_secid_currencies(secid_fph): # in which an primid has accounts
    accounts_fph_list, m = list_secid_accounts(secid_fph)
    currencies_fph_list = []
    for account_fph in accounts_fph_list:
        currencies_fph_list.append(get_account_currency(account_fph))
    return currencies_fph_list    # list


#==============================================================================
#

def list_secids(primid_fph):

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Retrieve the list of *secids* for this *primid*:
        cursor.execute(
            """
            SELECT secids_fph_list
            FROM primids
            WHERE entity_fph = ?
            """,
            (primid_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            secids_fph_list = []
        else:
            secids_fph_list = pickle.loads(result[0])
        return secids_fph_list





#==============================================================================
#
def get_parent_namespace(entity_fph): # for any entity

    return namespace_fph # string

#==============================================================================
# List all namespaces immediately below a specified namespace:
def list_child_namespaces(namespace_fph):

    return namespace_fph_list # list

#==============================================================================
# List all namespaces anywhere in the tree below the specified root namespace:
def list_all_namespaces(root_namespace_fph):

    return namespace_fph_list # list

#==============================================================================
# List all currencies named within the specified namespace:

def list_currencies_in_namespace(namespace_fph = ""):

    return currency_fph_list # list


#==============================================================================
# List all primids named within the specified namespace:
def list_primids_in_namespace(namespace_fph = ""):

    return primid_fph_list # list


#==============================================================================
# List all currencies named within the specified namespace:

def list_accounts_in_namespace(namespace_fph = ""):

    return currency_fph_list # list


#==============================================================================
# List all namespaces named within the specified namespace:
def list_namespaces_in_namespace(namespace_fph = ""):

    return namespace_fph_list # list


#==============================================================================
# List all namespaces named within the specified namespace:
def list_namespaces_below_namespace(namespace_fph = ""):

    return namespace_fph_list # list


#==============================================================================
# Move any entity to a new namespace (with the permission of both the entity's
# stewards/owner and the permission policy of the namespaces stewards).
def move_entity(entity_fph, destination_namespace_fph):

    entity_current_hrns = fph_to_hrns(entity_fph).split(".")
    entity_name = entity_current_hrns.pop([0]) # name = head of current HRNS
    destination_namespace_hrns = fph_to_hrns(destination_namespace_fph)
    entity_new_hrns = entity_name + destination_namespace_hrns

    # The entity's HRNS is updated but its FPH must remain the same. Therefore,
    # whereas the original FPH is a simple hash of the HRNS when first mapped,
    # any subsequent update to the HRNS must be mapped to the original FPH (and
    # vice versa).
    #
    # (1) the HRNS>FPH map must be updated
    # (2) the FPH>HRNS map must be updated
    #
    ##return new_hrns, error_message

    update_mapping(entity_current_hrns, entity_new_hrns)



#==============================================================================
## List the FPH of the currencies in which two agents both have an account:
def list_currencies_in_common_by_fph(a1_fph, a2_fph):
    return list(set(list_currencies(a1_fph)) & set(list_currencies(a2_fph)))

## List the HRNS of the currencies in which two agents both have an account:
def list_currencies_in_common_by_hrns(a1_fph, a2_fph):
    for currency_fph in list_currencies_in_common_by_fph(a1_fph, a2_fph):
        print(fph_to_hrns(currency_fph))

#==============================================================================
## Entities may be identified either by HRNS or by FPH. Given that these are
## very different in structure, they may be identified automatically:

def identify_entity(entity_identifier): # HRNS or FPH
    if not isinstance(entity_identifier, str):
        return "", "", "", ""
    if re_fph.match(entity_identifier): # this is an FPH
        entity_fph = entity_identifier
        entity_hrns = fph_to_hrns(entity_fph).strip()
        #entity_hrns = fph_to_hrns(entity_fph)
        if entity_hrns: # entity exists
            entity_type , m = get_entity_type(entity_fph)
            return entity_fph, entity_hrns, entity_type, ""
        else:
            return "", "", "", "Entity " + entity_fph + " does not exist.\n"
    elif re_hrns.match(entity_identifier): # this is an HRNS
        entity_hrns = entity_identifier
        entity_fph, m = hrns_to_fph(entity_identifier)
        if entity_fph: # entity exists
            entity_type , m = get_entity_type(entity_fph)
            return entity_fph, entity_hrns, entity_type, ""
        else:
            return "", "", "", "Entity " + entity_hrns + " does not exist.\n"
    else: # this is not an entity
        return "", "", "", entity_identifier + " is not an entity.\n"

#==============================================================================
##

def get_account_specific_properties(account_fph):

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT account_owner_fph, account_currency_fph, account_balance
            FROM accounts
            WHERE entity_fph = ?
            """,
            (account_fph,)
        )
        result = cursor.fetchone()
        cursor.close()

    if result is not None:
        owner_fph = result[0]
        currency_fph = result[1]
        balance = result[2]
    else: # no record for account_fph
        return "", "", 0, "Account not found"

    if not re_fph.match(owner_fph):
        return "", "", 0, "Invalid owner FPH: " + owner_fph

    if not re_fph.match(currency_fph):
        return "", "", 0, "Invalid currency FPH: " + currency_fph

    return currency_fph, owner_fph, balance, ""

#------------------------------------------------------------------------------
# Add a stewardship to a *primid* and a steward to a *namespace* or *currency*:

def add_stewardship(
        entity_fph,
        steward_fph
    ):
    if not re_fph.match(steward_fph):
        return steward_fph + " is not an FPH"

    if not re_fph.match(entity_fph):
        return entity_fph + " is not an FPH"

    errors = ""

    steward_etype, m = get_entity_type(steward_fph)
    if m:
        return m
    if steward_etype != "primid":
        return steward_fph + " is not a primid."

    entity_etype, m = get_entity_type(entity_fph)
    if m:
        return m
    if entity_etype == "namespace":
        table = " namespaces " # NB The spaces are important.
    elif entity_etype == "currency":
        table = " currencies " # NB The spaces are important.
    else:
        return entity_fph + " is " + entity_etype + " (not stewarded).\n"

    stewards_select_str = "SELECT stewards_fph_list " \
                        + "FROM" + table \
                        + "WHERE entity_fph = ?"

    stewards_update_str = "UPDATE" + table \
                        + "SET stewards_fph_list = ? " \
                        + "WHERE entity_fph = ?"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Add the stewarded entity's FPH to the *primid*'s stewardships list:
        cursor.execute(
            """
            SELECT stewardships_fph_list
            FROM primids
            WHERE entity_fph = ?
            """,
            (steward_fph,)
        )
        result = cursor.fetchone()
        stewardship_has_been_registered_already = False
        if result is not None:
            stewardships_fph_list = []
        else:
            stewardships_fph_list = pickle.loads(result[0])
            if entity_fph in stewardships_fph_list:
                stewardship_has_been_registered_already = True
        stewardships_fph_list.append(entity_fph)
        stewardships_fph_blob = pickle.dumps(stewardships_fph_list)
        cursor.execute(
            """
            UPDATE primids
            SET stewardships_fph_list = ?
            WHERE entity_fph = ?
            """,
            (stewardships_fph_blob, steward_fph)
        )

        # Add the steward's FPH to the *namespace* or *currency*:
        cursor.execute(stewards_select_str, (entity_fph,))
        result = cursor.fetchone()
        if result is None:
            stewards_fph_list = []
        else:
            stewards_fph_list = pickle.loads(result[0])
            if steward_fph in stewards_fph_list:
                if not stewardship_has_been_registered_already:
                    # Remove the inconsistent steward from entity:
                    stewardships_fph_list.remove(entity_fph)
                    cursor.execute(
                        """
                        UPDATE primids
                        SET stewardships_fph_list = ?
                        WHERE entity_fph = ?
                        """,
                        (stewardships_fph_blob, steward_fph)
                    )
                    errors += "Inconsistency found:\n" \
                           + "Steward " + steward_fph + " (" \
                           + fph_to_hrns(steward_fph) + ") has already been " \
                           + "registered for entity " + entity_fph + " (" \
                           + fph_to_hrns(entity_fph) + ") but stewardship " \
                           + "of entity " + entity_fph + " has not been " \
                           + "registered for steward " + steward_fph + "."
            else:
                if stewardship_has_been_registered_already:
                    # Remove the inconsistent stewardship from steward:
                    stewards_fph_list.remove(steward_fph)
                    errors += "Inconsistency found:\n" \
                           + "Stewardship of entity " + entity_fph + " (" \
                           + fph_to_hrns(entity_fph) + ") has already been " \
                           + "registered for steward " + steward_fph + " (" \
                           + fph_to_hrns(steward_fph) + ") but steward " \
                           + steward_fph + " has not already been " \
                           + "registered for entity " + entity_fph + "."
        stewards_fph_list.append(steward_fph)
        stewards_fph_blob = pickle.dumps(stewards_fph_list)
        cursor.execute(stewards_update_str, (stewards_fph_blob, entity_fph))
        conn.commit()
        cursor.close()

    return errors

# This can probably simplified by separating it into the following functions:
#   add_steward(entity_fph, steward_fph)
#       operating only on namespace/currency
#   add_stewardship(steward_fph, entity_fph)
#       operating only on steward
# combining these as:
#   def pair_steward_and_entity(steward_fph, entity_fph):
#       m1 = add_steward(entity_fph, steward_fph)
#       if not m1:
#           m2 = add_stewardship(steward_fph, entity_fph)
#           if m2:
#               m3 = remove_stewardship(steward_fph, entity_fph)
#               return m3
#           else:
#             return m2
#       else:
#           return m1

#------------------------------------------------------------------------------
# Remove single stewardship:

# Remove one or more steward(s) from entity:
def remove_stewards(entity_fph, *primids_fph):
    errors = ""
    #
    etype, m = get_entity_type(entity_fph)
    if m: # reject invalid FPH
#        errors += m
        return m
    if etype == "namespace":
        table = "namespaces"
    elif etype == "currency":
        table = "currencies"
    else:
        return entity_fph + " is " + etype + " so has no stewards.\n"
#        return errors # invalid invocation

    # Get a list of the entity's current stewards and extend it with any valid
    # primid FPH given:
    stewards_fph_list, m = list_stewards(entity_fph)
    if m:
        errors += m + "\n"
    any_primid_valid = False # flag
    for steward_fph in stewards_fph_list:
        etype, m = get_entity_type(steward_fph)
        if m:
            errors += m + "\n"
        else:
            stewards_fph_list.remove(primid_fph)
            any_primid_valid = True
    if not any_primid_valid: # there are no stewards to be added
        errors += "No valid primids were given as stewards\n"
        return errors

    primid_select_str = "SELECT stewardships_fph_list FROM primids " \
                      + "WHERE entity_fph = ?"
    primid_update_str = "UPDATE primids SET stewardships_fph_list = ? " \
                      + "WHERE entity_fph = ?"

    # If we reach this point the extended stewards list is complete so it can
    # be written # to the database:
    entity_update_str = "UPDATE " + table + " SET stewards_fph_list = ? " \
                      + "WHERE entity_fph = ?"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(entity_update_str)
        # Now we need to add the stewardships to the individual primids:
        for steward_fph in stewards_fph_list:
            cursor.execute(primid_select_str, (entity_fph,))
            result = cursor.fetchone()
            stewardships_fph_list = pickle.loads(result[0])
            stewardships_fph_list.remove(entity_fph)
            stewardships_fph_blob = pickle.dumps(stewardships_fph_list)
            cursor.execute(primid_update_str, stewardships_fph_blob)
        conn.commit()
        cursor.close()

    return ""

# Remove single stewardship from primid:
def remove_stewardship(primid_fph, entity_fph):
    e = remove_stewards(entity_fph, primids_fph)
    return e

#------------------------------------------------------------------------------
# List stewards of a namespace or currency:

def list_stewards(entity_fph):

    if not re_fph.match(entity_fph):
        return [], entity_fph + " is not an FPH"

    etype , m = get_entity_type(entity_fph)
    if etype == "namespace":
        table = " namespaces "
    elif etype == "currency":
        table = " currencies "
    else:
        return [], entity_fph + " is " + etype + " so has no steward"

    select_str = "SELECT stewards_fph_list " \
               + "FROM" + table \
               + "WHERE entity_fph = ?"

    update_str = "UPDATE" + table \
               + "SET stewards_fph_list = ? " \
               + "WHERE entity_fph = ?" \
               + "(stewards_fph_list, entity_fph)"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(select_str, (entity_fph,))
        result = cursor.fetchone()
        if result is not None:
            stewards_fph_list = pickle.loads(result[0])
        else:
            stewards_fph_list = []
            stewards_fph_blob = pickle.dumps(stewards_fph_list)
            cursor.execute(update_str, (entity_fph, stewards_fph_blob))
            conn.commit()
        cursor.close()

    return stewards_fph_list, ""

#------------------------------------------------------------------------------
# List stewardships of a *primid*:

def list_stewardships(primid_fph):

    if not re_fph.match(primid_fph):
        return [], primid_fph + " is not an FPH"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        #select_str = "SELECT stewardships_fph_list FROM primids " \
        #           + " WHERE entity_fph = ?"
        cursor.execute(
            """
            SELECT stewardships_fph_list
            FROM primids
            WHERE entity_fph = ?
            """,
            (primid_fph,)
        )
        results = cursor.fetchone()
        #cursor.execute(select_str, (primid_fph,))
        #stewardships_fph_blob = cursor.fetchone()[0]
        cursor.close()
    stewardships_fph_blob = results[0]
    stewardships_fph_list = pickle.loads(stewardships_fph_blob)
    stewardships = []
    for stewardhip_fph in stewardships_fph_list:
        stewardships.append(stewardhip_fph)

    return stewardships, ""



#==============================================================================
# List existing namespaces, specifying optionally a parent namespace.

def list_active_namespaces(ancestor_namespace_identifier = ""): # FPH or HRNS

    errors = ""

    if ancestor_namespace_identifier == "": # universal substrate namespace
        ancestor_fph = SUBSTRATE_FPH
        ancestor_hrns = ""
        etype = "namespace"
        m = ""
    else:
        ancestor_fph, \
        ancestor_hrns, \
        etype, \
        m = identify_entity(ancestor_namespace_identifier)
        if m or (etype != "namespace"):
            return [SUBSTRATE_FPH], m
        if m:
            errors += m


    # First the *namespace* trees are selected where the node root *namespace*
    # is active and has the specified ancestor *namespace* as its parent:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        #cursor.execute(
        #    """
        #    SELECT entity_fph
        #    FROM entities_common
        #    WHERE entity_type = 'namespace'
        #    AND active = 1;
        #    """
        #)
        cursor.execute(
            """
            SELECT entity_fph
            FROM entities_common
            WHERE entity_type = ?
            AND active = ?
            """,
            ("namespace", 1)
        )
        results = list(cursor.fetchall())
        cursor.close()

    # At this point we have a list of active namespaces sharing a specified
    # parent. Some of which will have descendants, and from among these the
    # remaining active namespaces will have to be identified.

    if results is None:
        #namespace_fph_list = [SUBSTRATE_FPH]
        return  [], "" #

    namespace_fph_list = []
    for result in results:
        namespace_fph = result[0]
        #print(namespace_fph)
        if re_fph.match(namespace_fph):
            namespace_hrns = fph_to_hrns(namespace_fph)
            branch = namespace_hrns.replace("." + ancestor_hrns, "")
            if branch:
                namespace_fph_list.append(namespace_fph)

    return namespace_fph_list, ""


#==============================================================================
# Get the *primid* to which a *secid* belongs:

def get_primid(secid_identifier):
    print("get_primid :: secid_id\t\t= " + secid_identifier)
    secid_fph, \
    secid_hrns, \
    etype, \
    m = identify_entity(secid_identifier)
    print("get_primid :: secid_fph\t\t= " + secid_fph)
    print("get_primid :: secid_hrns\t= " + secid_hrns)
    print("get_primid :: etype\t\t= " + etype)
    print("get_primid :: m\t\t\t= " + m)
    if m:
        return "", m
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT primid_fph
            FROM secids
            WHERE entity_fph = ?
            """,
            (secid_fph,)
        )
        result = cursor.fetchone()
    if result is not None:
        primid_fph = result[0]
        if isinstance(primid_fph, str) and re_fph.match(primid_fph):
            return primid_fph, ""
    return "", "No primid was found for " + secid_identifier



#==============================================================================
# List primids:

def list_primids(status = "all"):

    if status == "all":
        if_active = True
        if_inactive = True
    elif status == "active":
        if_active = True
        if_inactive = False
    elif status == "inactive":
        if_active = False
        if_inactive = True
    else:
        if_active = False
        if_inactive = False

    return_fph_list = []

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT entity_fph FROM primids")
        results = cursor.fetchall()
        for result in results:
            primid_fph = result[0]
            cursor.execute(
                "SELECT active FROM entities_common WHERE entity_fph = ?",
                (primid_fph,)
            )
            primid_row = cursor.fetchone()
            if primid_row is None:
                entity_is_active = False
            else:
                entity_is_active = primid_row[0]

            if entity_is_active and if_active:
                return_fph_list.append(primid_fph)
            if (not entity_is_active) and if_inactive:
                return_fph_list.append(primid_fph)

        cursor.close()

    return return_fph_list, ""

#==============================================================================

def email_to_primid(email):
    if not re_email.match(email):
        return ""
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT entity_fph FROM primids
            WHERE primid_email_1 = ? OR primid_email_2 = ?
            """,
            (email,email)
        )
        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            return result[0] # *primid* FPH
        else:
            return ""

#==============================================================================
