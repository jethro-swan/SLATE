import sqlite3
import random
import os
import pickle
from pathlib import Path
from string import ascii_lowercase

from app.core.constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
from app.core.constants import HUBS_DB
from app.core.constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from app.core.constants import SUBSTRATE_FPH
from app.core.constants import VERSION, CONFIG

from app.core.common import filename_timestamp as timestamp
from app.core.common import nshash
from app.core.common import unixtime_str

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from app.core.fph_hrns_maps import delete_fph_from_map

from app.core.dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from app.core.dbm_functions import dbm_create_map

from app.core.auth import auth_hash, check_auth_hash, generate_access_token

from app.core.regexp_list import *

from app.core.unix_functions import fcopy

from app.core.cctld_list import *

#------------------------------------------------------------------------------
# In NESTS the FPH has so far been formed as the hash of the FIP, but making it
# the hash of the HRNS instead will simplify compatibility between SLATE and
# NESTS and speed up the HRNS to FPH mapping without having any signifcant
# impact on the FPH to HRNS and FPH to FIP mappings.

#==============================================================================
def create_hubs_db():

    # This database is kept separate from the others because it needs to be
    # kept consistent with copies held across other hubs (according to rules
    # not yet defined):

    if os.path.exists(HUBS_DB):
        # If the database exists already, it is deleted after a time-stamped
        # copy has been saved.
        fcopy(HUBS_DB, DB_BKP_DIR + '/entities_' + timestamp() + '.db')
        os.remove(HUBS_DB)
    #
    with sqlite3.connect(HUBS_DB) as conn:
        cursor = conn.cursor()
        # The initial values for the following details are read from a
        # configuration file at the time of installation.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS hub (
                hub_id INTEGER PRIMARY KEY AUTOINCREMENT,
                subdomain TEXT DEFAULT '',
                must_be_archived INTEGER NOT NULL DEFAULT 1,
                administrators_fph_list BLOB,
                single_hub INTEGER NOT NULL DEFAULT 1,
                hub_members BLOB,
                synchronized_hubs BLOB,
                nests_extensions_enabled INTEGER NOT NULL DEFAULT 0,
                location_details BLOB,
                contact_details BLOB
            );
            """
        )

#==============================================================================
# Get hub mode:
#
# The operational mode is stored in an environment variable. Its value
# determines some aspects of the hub behaviour.

def get_hub_mode():
    hub_mode = os.environ.get("HUB_MODE")
    if hub_mode is None:
        return "omtrad"
    elif hub_mode in [
                        "slate_normal",
                        "slate_simple",
                        "slate_minimal",
                        "omtrad",
                        "nests"
                     ]:
        #print(hub_mode)
        return hub_mode
    else:
        return "omtrad"

# Get version number:
def get_version():
    with open(VERSION, "r") as v_file:
        version = v_file.read()
    return version


#==============================================================================
# Return site configuration item by key string:

def get_config():
    with open(CONFIG, "r") as cfg:
        c = cfg.readlines()
    config = {}
    for row in c:
#        print(row)
        r = row.split()
        config[r[0]] = r[1]
    return config




#==============================================================================
# Global data, flags, etc.









#==============================================================================
## Create the SQLite entities database:

def create_entities_db():

    if os.path.exists(ENTITIES_DB):
        # If the database exists already, it is deleted after a time-stamped
        # copy has been saved.
        fcopy(ENTITIES_DB, DB_BKP_DIR + '/entities_' + timestamp() + '.db')
        os.remove(ENTITIES_DB)

    # If this entity is a *private namespace* (one that has ramified from a
    # *primid* or *secid*, both that privacy and its owenerhip must be evident.
    # By default, the ownership is inherited from the parent *namespace* but may
    # be overridden.
    #
    # That ownership is not the same as a stewardship. If a *namespace* has an
    # owner it needs no stewards and, if it is an *identity* serving as the
    # root *namespace* of such a tree it cannot have stewards, but *namespaces*
    # created as children/descendants of such a root may have stewards if the
    # owner chooses to invite them.

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # A table is created for the entities' common properties:
        cursor.execute(
            """
    	    CREATE TABLE IF NOT EXISTS entities_common (
                entity_fph TEXT PRIMARY KEY,
                parent_namespace_fph TEXT,
                entity_type TEXT,
                default_currency_fph TEXT DEFAULT '',
                private INTEGER NOT NULL DEFAULT 0,
                owner_fph TEXT DEFAULT '',
                active INTEGER NOT NULL DEFAULT 1
            );
            """
        )
        # Create namespaces table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS namespaces (
                entity_fph TEXT PRIMARY KEY,
                stewards_fph_list BLOB,
                sandbox INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        # Create primids table:
#        cursor.execute(
#            """
#    	    CREATE TABLE IF NOT EXISTS primids (
#                entity_fph TEXT PRIMARY KEY,
#                primid_realname TEXT,
#                primid_email_1_hash TEXT NOT NULL,
#                primid_email_1_hash TEXT,
#                secids_fph_list BLOB,
#                accounts_fph_list BLOB,
#                stewardships_fph_list BLOB,
#                password_hash TEXT NOT NULL,
#                pin TEXT,
#                access_token_hash TEXT
#            );
#            """
#        )

        # NB, since a *primid* or *secid* can serve as the root private
        # *namespace*, a default *currency* must be specified.
        #
        # Create primids table:
        cursor.execute(
            """
    	    CREATE TABLE IF NOT EXISTS primids (
                entity_fph TEXT PRIMARY KEY,
                primid_realname TEXT,
                primid_email_1_hash TEXT NOT NULL,
                primid_email_2_hash TEXT,
                secids_fph_list BLOB,
                ahids_fph_list BLOB,
                accounts_fph_list BLOB,
                pmap BLOB,
                stewardships_fph_list BLOB,
                password_hash BLOB NOT NULL,
                pin TEXT,
                access_token_hash BLOB,
                administrator INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        # Create secids table:
        #
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS secids (
                entity_fph TEXT,
                primid_fph TEXT,
                accounts_fph_list BLOB
            );
            """
        )
        # Create ahds (*account-holder identities*) table:
        #
        # Unlike *secids* or *primids", an *ahid* can have only one *account*
        # in each *currency*. Therefore, the *accounts* belonging to each
        # *ahid* are mapped from *currencies* in a dictionary:
        #   {
        #       currency1_hrns : account1_fph,
        #       currency2_hrns : account2_fph,
        #       ...
        #   }
        #
##        cursor.execute(
##            """
##            CREATE TABLE IF NOT EXISTS ahids (
##                entity_fph TEXT,
##                primid_fph TEXT,
##                pairing_map BLOB
##           );
##            """
##        )



        # Create currencies table:
        #
        # Added 2025-03-18:
        #   category TEXT       currency type
        #
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS currencies (
                entity_fph TEXT PRIMARY KEY,
                currency_prefix TEXT,
                currency_suffix TEXT,
                default_account_name TEXT DEFAULT 'local',
                stewards_fph_list BLOB,
                sandbox INTEGER NOT NULL DEFAULT 0,
                category TEXT
            );
            """
        )
        # Create accounts table:
        #
        # Added 2025-03-18:
        #   type TEXT       currency type
        #   vector BLOB
        #   vector_map BLOB
        #   matrix BLOB
        #   matrix_map BLOB
        #   ts_pointer BLOB
        #   volume INTEGER NOT NULL DEFAULT 0
        #
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                entity_fph TEXT PRIMARY KEY,
                account_owner_fph TEXT NOT NULL,
                account_ahid_fph TEXT NOT NULL DEFAULT "",
                account_currency_fph TEXT NOT NULL,
                account_balance INTEGER NOT NULL DEFAULT 0,
                volume INTEGER NOT NULL DEFAULT 0,
                type TEXT,
                vector BLOB,
                vector_map BLOB,
                matrix BLOB,
                matrix_map BLOB,
                ts_pointer BLOB
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
## Entities may be identified either by HRNS or by FPH. Given that these are
## very different in structure, they may be identified automatically:

def identify_entity(entity_identifier): # HRNS or FPH

    if entity_identifier is None:
        entity_identifier = ""
#        return "", "", "", "entity_identifier" + str(entity_identifier)

    if not isinstance(entity_identifier, str):
        entity_identifier = ""

#        return "", "", "", str(entity_identifier) + " is not a string\n"

#    if type(entity_identifier) != str:
#        return "", "", "", entity_identifier + " is not a string\n"


    entity_identifier = entity_identifier.strip()

    if entity_identifier == SUBSTRATE_FPH:
        return entity_identifier, "", "namespace", ""

    if re_fph.match(entity_identifier): # this is an FPH
        entity_fph = entity_identifier.strip()
        entity_hrns = fph_to_hrns(entity_fph)
        if entity_hrns: # entity exists
            entity_type, m = get_entity_type(entity_fph)
            if m:
                return "", "", "", m
            return entity_fph, entity_hrns, entity_type, ""
        else:
            return "", "", "", "Entity " + entity_fph + " does not exist\n"
    elif re_hrns.match(entity_identifier): # this is an HRNS
        entity_hrns = entity_identifier.strip()
        entity_fph, m = hrns_to_fph(entity_identifier)
        if m:
            return "", "", "", m
        if entity_fph: # entity exists
            entity_type, m = get_entity_type(entity_fph)
            if m:
                return "", "", "", m
            return entity_fph, entity_hrns, entity_type, ""
        else:
            return "", "", "", "Entity " + entity_hrns + " does not exist\n"
    else: # this is not an entity
        return "", "", "", ""

        # NB, if a message is returned here it will cause misdirection in the
        # "/register" endpoint (and possibly others) so for the time being an
        # empty string is returned. This can be addressed later if necessary.


#==============================================================================
## Get namespace owner
#
# Here, a *namespace* may also be a *primid* or *secid*.

def get_private_namespace_details(namespace_identifier):

    namespace_fph, \
    namespace_hrns, \
    namespace_type, \
    m = identify_entity(namespace_identifier)

    if not (namespace_type in ["namespace", "primid", "secid"]):
        return False, "", "Entity cannot be a private namespace"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT private, namespace_owner
            FROM entities_common
            WHERE entity_fph = ?
            """,
            (namespace_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
        if result is None:
            return False, "", "Entity not identifiable as private namespace"
        else:
            private = result[0]
            owner_fph = result[1]
            if private:
                return private, owner_fph, ""
            else:
                return False, "", "Entity is not a private namespace"

#------------------------------------------------------------------------------

def set_private_namespace_owner(namespace_identifier, identity_identifier):

    namespace_fph, \
    namespace_hrns, \
    namespace_type, \
    m = identify_entity(namespace_identifier)

    if (namespace_type != "primid") and (namespace_type != "secid"):
        return "Entity cannot be a private namespace"

    identity_fph, \
    identity_hrns, \
    identity_type, \
    m = identify_entity(identity_identifier)

#    if (identity_type != "primid") and (identity_type != "secid"):
#        return "Entity is not a namespace type"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE entities_common
            SET owner_fph = ?
            WHERE entity_fph = ?
            """,
            (identity_fph, namespace_fph)
        )
        conn.commit()
        cursor.close()

    return ""



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
        default_currency_fph,
        private, # boolean
        owner_fph,
        active # boolean
    ):
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO entities_common (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                default_currency_fph,
                private,
                owner_fph,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                default_currency_fph,
                int(private),
                owner_fph,
                int(active)
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

    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(entity_id)
    if m:
        return "", "", "", False, "", False, m

    #if not re_fph.match(entity_fph):
    #    return entity_fph, "", False, entity + " is not an FPH"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT parent_namespace_fph, private, owner_fph, active
            FROM entities_common
            WHERE entity_fph = ?
            """,
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return entity_fph, "", "", False, "", False, "Not found"

    parent_ns_fph = result[0]
    private = result[1]
    owner_fph = result[2]
    active = result[3]
    return entity_fph, parent_ns_fph, etype, private, owner_fph, active, ""

#==============================================================================
## Check whether an entity is currently active:

def entity_is_active(entity_id):

    entity_fph, \
    entity_hrns, \
    entity_type, \
    m = identify_entity(entity_id)
    if m:
        return False, m

    entity_fph, \
    parent_namespace_fph, \
    entity_type, \
    private, \
    owner_fph, \
    active, \
    m = get_entity_common_properties(entity_fph)
    return active, m


#==============================================================================
## Check whether a *namespace* is private:

def privacy(entity_id): # *namespace*, *primid* or *secid*

    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(entity_id)
    if m:
        return False
    if not (etype in ["namespace", "primid", "secid"]):
        return False

    entity_fph, \
    parent_namespace_fph, \
    entity_type, \
    private, \
    owner_fph, \
    active, \
    m = get_entity_common_properties(entity_fph)
    if m:
        return False
    return private

#==============================================================================
## Get owner of entity:
def get_owner(entity_id):

    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(entity_id)
    if m:
        return ""
    if not (etype in ["account", "namespace", "primid", "secid"]):
        return ""

    entity_fph, \
    parent_namespace_fph, \
    entity_type, \
    private, \
    owner_fph, \
    active, \
    m = get_entity_common_properties(entity_fph)
    if m:
        return False
    return owner_fph











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
#    print(entity_fph + " >>> " + fph_to_hrns(entity_fph))
    #print(result)
    if result is not None:
        entity_type = result[0]
#        print(result[0])
        return entity_type, ""
#            if entity_type in [
#                                "namespace",
#                                "currency",
#                                "primid",
#                                "secid",
#                                "account"
#                              ]:
#                return entity_type, ""
#            else:
#                return "", ""
    else:
        return "", "Type cannot be identified for " + fph_to_hrns(entity_fph)

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



def list_currency_accounts(currency_id):
    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_id)
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_fph FROM currency_accounts WHERE currency_fph = ?",
            (currency_fph,)
        )
        results = cursor.fetchall()
        cursor.close()
        #print(results)
    if results is not None:
        accounts = []
        for result in results:
            accounts.append(result[0])
        return accounts
    else:
        return []






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
        update_str += "primid_email_1_hash = ?, "
        values_str += auth_hash(primid_email_1_hash) + ", "
        update_needed = True
    else:
        errors += primid_email_1 + " is not a valid email address"
    if primid_email_2 and re_email.match(primid_email_2):
        update_str += "primid_email_2_hash = ?, "
        values_str += auth_hash(primid_email_2_hash) + ", "
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
        pin
#        pin,
#        access_token
    ):
    errors = ""
    if not re_fph.match(primid_fph):
        errors += primid_fph + " is not an FPH\n"
        return errors
    etype, m = get_entity_type(primid_fph)
    if m:
        errors += m + "\n"
    if etype != "primid":
        errors += primid_fph + " is not a primid\n"
        return errors
    update_needed = False
    if password:
        password_hash = auth_hash(password)
    else:
        errors += "No password provided\n"
        return errors
    if not (pin and re_pin.match(pin)):
        errors += "PIN value invalid"
        return errors

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
                   "UPDATE primids " + \
                   "SET password_hash = ?, pin = ? " + \
                   "WHERE entity_fph = ?",
                   (password_hash, pin, primid_fph)
               )

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
        return False, False, "", "", "", 0, 0, "Invalid FPH: " + account_fph

    #account_fph = "'" + account_fph + "'"
    # wrapped to enable SQLite to accept it.

    entity_fph, \
    parent_namespace_fph, \
    entity_type, \
    private, \
    owner_fph, \
    active, \
    m = get_entity_common_properties(account_fph)
    if m:
        return False, False, "", "", "", 0, 0, m
    if entity_type != "account":
        return False, False, "", "", "", 0, 0, account_fph + " is not ccount"

    currency_fph, \
    owner_fph, \
    ahid_fph, \
    balance, \
    volume, \
    m = get_account_specific_properties(account_fph)
    if m:
        return False, False, "", "", "",0, 0, m
    if volume is None:
        volume = 0

    return True, active, currency_fph, owner_fph, ahid_fph, balance, volume, ""

#==============================================================================









def namespace_status(namespace_fph):

    if not re_fph.match(namespace_fph):
        return "", "", [], "Invalid FPH: " + namespace_fph

    entity_fph, \
    parent_namespace_fph, \
    entity_type, \
    private, \
    active, \
    m = get_entity_common_properties(namespace_fph)
    if m:
        return False, False, [], m
#    if entity_type != "namespace":
#        return False, False, [], namespace_fph + " is not a namespace"

    stewards_list, m = list_stewards(namespace_fph)
    if m:
        return False, private, False, [], m

    return True, private, active, stewards_list, ""










#==============================================================================
# A new *primid* is created in the specified namespace. This function is used
# only at the point of registration.

def new_primid(
        username,
        parent_namespace_fph,
        realname,
        email_address_1,
        email_address_2,
        password,
        pin
    ):

    errors = ""

    if not re_pin.match(pin):
        return "", "", "", "Invalid PIN provided."

    etype, m = get_entity_type(parent_namespace_fph)
    if m:
        return "", "", "", m # parent_namespace_fph is invalid
##    if etype != "namespace":
##        return "", "", "", parent_namespace_fph + " is not a namespace"
    namespace_hrns = fph_to_hrns(parent_namespace_fph)
    primid_hrns = username + "." + namespace_hrns

    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(primid_hrns)
#    if m:
#        print(m)
    if entity_fph:
        return "", "", "", primid_hrns + " exists already (" + etype + ")"

    primid_fph, m = hrns_to_fph(primid_hrns)
    if m:
        delete_fph_from_map(primid_fph)
        return "", "", "", m

    if realname:
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

    #get_default_currency(entity_identifier)

    add_entity_common_properties(
        primid_fph,
        parent_namespace_fph,
        "primid",
        get_default_currency(parent_namespace_fph),
        True,       # This is a *primid* so the root of a private *namesapce*
        primid_fph, # owned by this *primid*.
        True
    )

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO primids (
                entity_fph,
                primid_realname,
                primid_email_1_hash,
                primid_email_2_hash,
                secids_fph_list,
                pmap,
                accounts_fph_list,
                stewardships_fph_list,
                password_hash,
                pin,
                access_token_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                primid_fph,
                realname,
                auth_hash(email_address_1),
                auth_hash(email_address_2),
                pickle.dumps(secids_fph_list),          # empty list
                pickle.dumps({}),                       # empty dictionary
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
#    if fph_to_hrns(nshash(secid_hrns)):
#        return "", "", "A entity " + secid_hrns + " is already registered"
    #
    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(secid_hrns)
#    if m:
#        print(m)
    if entity_fph:
        return "", "", secid_hrns + " exists already (" + etype + ")"

    else:
        secid_fph, m = hrns_to_fph(secid_hrns)
        if m:
            return "", "", m

    add_entity_common_properties(
        secid_fph,
        parent_namespace_fph,
        "secid",
        get_default_currency(parent_namespace_fph),
        True,       # this is a *secid* so the root of a private *namesapce*
        secid_fph,  # owned by this *secid*.
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
            #secids_fph_blob = pickle.dumps(secids_fph_list)
        else:
            secids_fph_blob = result[0]
            secids_fph_list = pickle.loads(secids_fph_blob)
        secids_fph_list.append(secid_fph)
        secids_fph_blob = pickle.dumps(secids_fph_list)
        cursor.execute(
            """
            UPDATE primids
            SET secids_fph_list = ?
            WHERE entity_fph = ?
            """,
            (secids_fph_blob, primid_fph)
        )
        conn.commit()
        cursor.close()

        # TEST STUFF
        with open("secid_creation_dump.txt", "a") as f:
            f.write(
                "secid " + secid_hrns + " (" + secid_fph + ") " \
                + "added for primid " + fph_to_hrns(primid_fph) \
                + " (" + primid_fph + ")\n"
            )
        # END OF TEST STUFF

    return secid_fph, secid_hrns, ""

#==============================================================================
## A new namespace is created:

def new_namespace(
        namespace_name,
        parent_namespace_fph,
        default_currency_fph,
        initial_steward_fph
    ):
    # The substrate is a special case of parent *namespace* (nameless):
    if parent_namespace_fph == SUBSTRATE_FPH:
        parent_namespace_hrns = ""
        etype = "namespace"
    else:
        parent_namespace_fph, \
        parent_namespace_hrns, \
        etype, \
        m = identify_entity(parent_namespace_fph)
    if parent_namespace_fph == "":
        return "", "", "Parent namespace does not exist"

    if not re_slatename.match(namespace_name):
        return "", "", namespace_name + " is not a valid name"

    if parent_namespace_hrns:
        namespace_hrns = namespace_name + "." + parent_namespace_hrns
    else:
        namespace_hrns = namespace_name

    existing_namespace_fph, \
    existing_namespace_hrns, \
    etype, \
    m = identify_entity(namespace_hrns)
#    if existing_namespace_fph:
#        return "", "", "Entity " + namespace_hrns + " is already registered"
    #
    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(namespace_hrns)
#    if m:
#        print(m)
    if entity_fph:
        return "", "", namespace_hrns + " exists already (" + etype + ")"

    # The HRNS and FPH are added to the FPH>HRNS and HRNS>FPH maps:
    namespace_fph, m = hrns_to_fph(namespace_hrns)

    add_entity_common_properties(
        namespace_fph,
        parent_namespace_fph,
        "namespace",
        default_currency_fph,
        privacy(parent_namespace_fph), # the parent *namespace* MAY be private
        get_owner(parent_namespace_fph),
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
        currency_suffix,
        default_account_name
    ):
    # The initial *account* in this *currency* is assigned to its initial
    # steward (which must exist already).

    parent_namespace_fph, \
    parent_namespace_hrns, \
    etype, \
    m = identify_entity(parent_namespace_fph)
    if parent_namespace_fph == "":
        return "", "", "Parent namespace does not exist"

    if not re_slatename.match(currency_name):
        return "", "", currency_name + " is not a valid name"

    if default_account_name:
        if not re_slatename.match(default_account_name):
            return "", "", default_account_name + " is not a valid name"

    currency_hrns = currency_name + "." + parent_namespace_hrns

    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(currency_hrns)
#    if m:
#        print(m)
    if entity_fph:
        return "", "", currency_hrns + " exists already (" + etype + ")"

    currency_fph, m = hrns_to_fph(currency_hrns)

    add_entity_common_properties(
        currency_fph,
        parent_namespace_fph,
        "currency",             # entity type
        "",                     # Not applicable
        False,                  # Not applicable
        "",                     # Not applicable
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
                default_account_name,
                stewards_fph_list
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                currency_fph,
                currency_prefix,
                currency_suffix,
                default_account_name,
                pickle.dumps([initial_steward_fph])
            )
        )
        cursor.execute(
            """
            SELECT stewardships_fph_list
            FROM primids
            WHERE entity_fph = ?
            """,
            (initial_steward_fph,)
        )
        result = cursor.fetchone()
        if result is not None:
            stewardships_fph_blob = result[0]
            stewardships_fph_list = pickle.loads(stewardships_fph_blob)
        else:
            stewardships_fph_list = []
        if not (currency_fph in stewardships_fph_list):
            stewardships_fph_list.append(currency_fph)
            stewardships_fph_blob = pickle.dumps(stewardships_fph_list)
            cursor.execute(
                """
                UPDATE primids
                SET stewardships_fph_list = ?
                WHERE entity_fph = ?
                """,
                (stewardships_fph_blob, initial_steward_fph)
            )
            conn.commit()
        cursor.close()

    return currency_fph, currency_hrns, ""

#==============================================================================
## A new account is created in a specified currency:

def new_account(
        account_name,
        parent_namespace_fph,
        owner_fph,      # (Owner may be a *primid* or a *secid*)
        ahid_fph,       # *account-holder* for omtrad mode.
        currency_fph
    ):

    if not re_fph.match(parent_namespace_fph):
        return "", "", "Invalid parent namespace FPH: " + parent_namespace_fph

    if not re_fph.match(owner_fph):
        return "", "", "Invalid owner FPH: " + owner_fph

    parent_namespace_hrns = fph_to_hrns(parent_namespace_fph)
    account_hrns = account_name + "." + parent_namespace_hrns

    owner_fph, \
    owner_hrns, \
    owner_type, \
    m = identify_entity(owner_fph)

    if owner_type == "primid":
        a_table = "primids"
    elif owner_type == "secid":
        a_table = "secids"
    else:
        return "", "", owner_fph + " is not an agent"

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_fph)
    if (etype != "currency"):
        return "", "", currency_fph + " is not a currency"

    currency_fph, \
    currency_hrns, \
    prefix, \
    suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_specific_properties(currency_fph)

    if account_name == "":
        account_name = default_account_name

#    if fph_to_hrns(nshash(account_hrns)):
#        return "", "", "An entity " + account_hrns + " is already registered"
    #
    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(account_hrns)
#    if m:
#        print(m)
    if entity_fph:
        return "", "", account_hrns + " exists already (" + etype + ")"

    account_fph, m = hrns_to_fph(account_hrns)

    add_entity_common_properties(
        account_fph,
        owner_fph, ## NB, currently stored in *accounts* table
        "account",
        "", # empty because an *account* does not have a default *currency*
        False, # not applicable to *account*
        owner_fph, ## NB, in future may be stored in *entities_common* table
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
                account_ahid_fph,
                account_currency_fph,
                account_balance
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                account_fph,
                owner_fph,      # Owner may be either *primid* or *secid"
                ahid_fph,
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
        cursor.execute(select_string, (owner_fph,))
        result = cursor.fetchone()
        accounts_fph_blob = result[0]
        accounts_fph_list = pickle.loads(accounts_fph_blob)
        accounts_fph_list.append(account_fph)
        accounts_fph_blob = pickle.dumps(accounts_fph_list)
        cursor.execute(update_string, (accounts_fph_blob, owner_fph))

        conn.commit()

        cursor.close()

        add_account_to_currency(account_fph, currency_fph)

    if m:
        return "", "", m
    else:
        return account_fph, account_hrns, ""

#==============================================================================
##

def get_namespace_specific_properties(namespace_identifier):

    namespace_fph, \
    namespace_hrns, \
    namespace_type, \
    m = identify_entity(namespace_identifier)
    if m:
        return "", [], False, m

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Add the stewarded entity's FPH to the *primid*'s stewardships list:
        cursor.execute(
            """
            SELECT stewards_fph_list, sandbox
            FROM namespaces
            WHERE entity_fph = ?
            """,
            (namespace_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            m = "Namespace " + fph_to_hrns(namespace_fph) + " not found"
            return "", [], False, m
        else:
            stewards_fph_blob = result[0]
            sandbox = result[1]
            stewards_list = pickle.loads(stewards_fph_blob)
        cursor.execute(
            """
            SELECT default_currency_fph
            FROM entities_common
            WHERE entity_fph = ?
            """,
            (namespace_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            return "", [], False, "Default currency cannot be identified"
        else:
            default_currency_fph = result[0]
        return default_currency_fph, stewards_list, sandbox, ""

#==============================================================================
## Set the default *currency* for the *namespace* (including that of a
## *primid-namespace* or *secid-namespace*).

def set_default_currency(entity_identifier, currency_identifier):

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_identifier)
    if m:
        return m
    if not currency_fph:
        return "Currency cannot be identified"

    entity_fph, \
    entity_hrns, \
    entity_type, \
    m = identify_entity(entity_identifier)
    if m:
        return m
    if not entity_fph:
        return "Entity cannot be identified"

    # The "default_currency_fph" field has now been moved from the "namespaces"
    # table to the "entities_common" table.

# 2025-04-08: *currency* added ti list
    if not (entity_type in ["namespace", "primid", "secid", "currency"]):
        return fph_to_hrns(entity_identifier) + " is not a namespace type"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE entities_common
            SET default_currency_fph = ?
            WHERE entity_fph = ?
            """,
            (currency_fph, entity_fph)
        )
        conn.commit()
        cursor.close()

    return ""

#------------------------------------------------------------------------------
def get_default_currency(entity_identifier):

    entity_fph, \
    entity_hrns, \
    entity_type, \
    m = identify_entity(entity_identifier)

    # 2025-04-08: *currency* added ti list
    if not (entity_type in ["namespace", "primid", "secid", "currency"]):
        return fph_to_hrns(entity_identifier) + " is not a namespace type"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT default_currency_fph
            FROM entities_common
            WHERE entity_fph = ?
            """,
            (entity_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            return "Default currency cannot be identified"
        else:
            return result[0]

#==============================================================================
##

def get_currency_specific_properties(currency_identifier):

    currency_fph, \
    currency_hrns, \
    entity_type, \
    m = identify_entity(currency_identifier)
    if m:
        return "", "", "", "", "", "", m

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Add the stewarded entity's FPH to the *primid*'s stewardships list:
        cursor.execute(
            """
            SELECT currency_prefix, currency_suffix, default_account_name,
                   stewards_fph_list
            FROM currencies
            WHERE entity_fph = ?
            """,
            (currency_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        m = "Currency " + fph_to_hrns(currency_fph) + " not found"
        return "", "", "", "", "", "", m
    else:
        prefix = result[0]
        suffix = result[1]
        default_account_name = result[2]
        stewards_fph_blob = result[3]
        stewards_list = pickle.loads(stewards_fph_blob)

        return currency_fph, currency_hrns, prefix, suffix, \
               default_account_name, stewards_list, ""

#==============================================================================
##
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

#            print(accounts_fph_list)

    return accounts_fph_list, ""    # list + message

# The following is a temporary solution pending cleanup and merger:

def list_primid_accounts_in_currency(primid_fph, currency_fph):

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT accounts_fph_list
            FROM primids
            WHERE entity_fph = ?, currency_fph = ?
            """,
            (primid_fph,currency_fph)
        )
        result = cursor.fetchone()
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

#            print(accounts_fph_list)

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
            cursor.close()
            accounts_fph_blob = result[0]
            accounts_fph_list = pickle.loads(accounts_fph_blob)

#            print(accounts_fph_list)

        return accounts_fph_list, ""    # list + message

#==============================================================================
##
#
# NB  The two functions above may be combined into a single function:

def list_agent_accounts(agent_fph):

    etype, m = get_entity_type(agent_fph)

    if etype == "primid":
        accounts_fph_list, m = list_primid_accounts(agent_fph)
        if m:
            return [], m
    elif etype == "secid":
        accounts_fph_list, m = list_secid_accounts(agent_fph)
        if m:
            return [], m
    else:
        #accounts_fph_list = []
        m = agent_fph + " is not an identity of either type"
        if m:
            return [], m

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
        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            currency_fph = result[0]
        else:
            currency_fph = ""
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
        # FIX: The results retrieved are currently tuples where they should be
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
            (currency_fph, primid_fph)
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





def list_agent_currencies(agent_identifier):

    agent_fph, \
    agent_hrns, \
    etype, \
    m = identify_entity(agent_identifier)

    if etype == "primid":
        return list_primid_currencies(agent_fph)
    elif etype == "secid":
        return list_secid_currencies(agent_fph)








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

def list_ahids(primid_fph):

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Retrieve the list of *ahids* for this *primid*:
        cursor.execute(
            """
            SELECT ahids_fph_list
            FROM primids
            WHERE entity_fph = ?
            """,
            (primid_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            ahids_fph_list = []
        elif result[0] is not None:
            ahids_fph_list = pickle.loads(result[0])
            return ahids_fph_list
        else:
            return []







#==============================================================================
#
def get_parent_namespace(entity_fph): # for any entity

    return namespace_fph # string

#==============================================================================
# List all namespaces immediately below a specified namespace:
def list_child_namespaces(namespace_fph):

    return namespace_fph_list # list

#==============================================================================
# List all namespaces:
def list_all_namespaces():

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        #cursor.execute(
        #    """
        #    SELECT entity_fph, default_currency_fph
        #    FROM namespaces
        #    """
        #)
        cursor.execute(
            """
            SELECT entity_fph
            FROM namespaces
            """
        )
        result_list = cursor.fetchall()
        if result_list is None:
            return [], "Gremlin alert"
        active_namespaces = []
        for namespace in result_list:
            namespace_fph = namespace[0]
            #print(namespace_fph)
            cursor.execute(
                """
                SELECT active
                FROM entities_common
                WHERE entity_fph = ?
                """,
                (namespace_fph,)
            )
            result = cursor.fetchone()
            if result[0]:
                active_namespaces.append(namespace_fph)
        cursor.close()

    return active_namespaces, ""

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
# List all namespaces:
def list_all_namespaces():

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT entity_fph FROM namespaces",
            (namespace_fph,)
        )
        result = cursor.fetchall()
        cursor.close()
        if result is None:
            return []
        else:
            return result

# List all currencies:
def list_all_currencies():

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT entity_fph FROM currencies",
            (namespace_fph,)
        )
        result = cursor.fetchall()
        cursor.close()
        if result is None:
            return []
        else:
            return result


# List all currencies:
def list_all_currencies():

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT entity_fph FROM currencies",
            (namespace_fph,)
        )
        result = cursor.fetchall()
        cursor.close()
        if result is None:
            return []
        else:
            return result






#==============================================================================
# List all *namespaces* named within the specified *namespace*:
def list_namespaces_in_namespace(namespace_fph = ""):

    return namespace_fph_list # list


#==============================================================================
# List all *namespaces* nbelow the specified *namespace*:
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
##

def get_account_specific_properties(account_fph):

    #print("account = " + account_fph + " > " + fph_to_hrns(account_fph))

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT account_owner_fph,
                   account_ahid_fph,
                   account_currency_fph,
                   account_balance,
                   volume
            FROM accounts
            WHERE entity_fph = ?
            """,
            (account_fph,)
        )
        result = cursor.fetchone()
        cursor.close()

    if result is not None:
        owner_fph = result[0]
        ahid_fph = result[1]
        currency_fph = result[2]
        balance = result[3]
        volume = result[4]
    else: # no record for account_fph
        return "", "", "", 0, 0, "Account not found"

    if not re_fph.match(owner_fph):
        return "", "", "", 0, 0, "Invalid owner FPH: " + owner_fph

    if not re_fph.match(currency_fph):
        return "", "", "", 0, 0, "Invalid currency FPH: " + currency_fph

    return currency_fph, owner_fph, ahid_fph, balance, volume, ""

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
def remove_stewardship(primids_fph, entity_fph):
    e = remove_stewards(entity_fph, primids_fph)
    return e




def remove_steward(entity_id, removing_steward_id, removed_steward_id):

    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(entity_id)
    if m:
        return m
    if entity_fph == "":
        return "Entity does not exist"
    if etype == "namespace":
        table = "namespaces"
    elif etype == "currency":
        table = "currencies"
    else:
        return "Entity is not a stewarded type"

    removing_steward_fph, \
    removing_steward_hrns, \
    etype, \
    m = identify_entity(removing_steward_id)
    if m:
        return m
    if removing_steward_fph == "":
        return "Removing steward does not exist"

    removed_steward_fph, \
    removed_steward_hrns, \
    etype, \
    m = identify_entity(removed_steward_id)
    if m:
        return m
    if removed_steward_fph == "":
        return "Steward to be removed does not exist"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # First get the list of stewards for this entity:
        cursor.execute(
            "SELECT stewards_fph_list FROM " + table + " WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        stewards_fph_list = pickle.loads(result[0])
        if not (removing_steward_fph in stewards_fph_list):
            cursor.close()
            return removing_steward_hrns + " is not steward of " + entity_hrns
        elif not (removed_steward_fph in stewards_fph_list):
            cursor.close()
            return removed_steward_hrns + " is not steward of " + entity_hrns
        # The steward can now be removed:
        if removed_steward_fph in stewards_fph_list:
            stewards_fph_list.remove(removed_steward_fph)
        stewards_fph_blob = pickle.dumps(stewards_fph_list)
        cursor.execute(
            "UPDATE " + table + " SET stewards_fph_list = ? " \
            + "WHERE entity_fph = ?",
            (stewards_fph_blob, entity_fph)
        )
        # The entity can now be removed from the removed steward's list of
        # stewardships:
        cursor.execute(
            "SELECT stewardships_fph_list FROM primids WHERE entity_fph = ?",
            (removed_steward_fph,)
        )
        result = cursor.fetchone()
        stewardships_fph_list = pickle.loads(result[0])
        if entity_fph in stewardships_fph_list:
            stewardships_fph_list.remove(entity_fph)
        stewardships_fph_blob = pickle.dumps(stewardships_fph_list)
        cursor.execute(
            "UPDATE primids SET stewardships_fph_list = ? " \
            + "WHERE entity_fph = ?",
            (stewardships_fph_blob, removed_steward_fph)
        )
        conn.commit()
        cursor.close()

    return ""

#------------------------------------------------------------------------------
# List stewards of a namespace or currency:

def list_stewards(entity_fph):

    if not re_fph.match(entity_fph):
        return [], entity_fph + " is not an FPH"

    etype, m = get_entity_type(entity_fph)
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
        result = cursor.fetchone()
        #cursor.execute(select_str, (primid_fph,))
        #stewardships_fph_blob = cursor.fetchone()[0]
    if result is None:
        stewardships_fph_list = []
        stewardships_fph_blob = pickle.dumps(stewardships_fph_list)
        cursor.execute(
            """
            UPDATE primids
            SET stewardships_fph_list = ?
            WHERE entity_fph = ?
            """,
            (stewardships_fph_blob, primid_fph)
        )
        conn.commit()
        cursor.close()
        return [], "The primid " + primid_fph + " has no stewardships."
    else:
        cursor.close()
        stewardships_fph_blob = result[0]
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

def get_primid(id_identifier): # *secid* or *ahid*
    id_fph, \
    id_hrns, \
    etype, \
    m = identify_entity(id_identifier)
    if m:
        return "", m
    if etype == "ahid":
        return get_ahid_primid(id_fph)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT primid_fph
            FROM secids
            WHERE entity_fph = ?
            """,
            (id_fph,)
        )
        result = cursor.fetchone()
    if result is not None:
        primid_fph = result[0]
        if isinstance(primid_fph, str) and re_fph.match(primid_fph):
            return primid_fph, ""
    return "", "No primid was found for " + id_identifier

#==============================================================================

def get_ahid_primid(ahid_hrns):
    # (1) Each *ahid* belongs to one *primid*
    # (2) Each *primid* may have any number of *ahid*
    # (3) A *primid* may belong to itself as an *ahid*
    ahid_fph, wom, etype, m = identify_entity(ahid_hrns)
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
#    if (result is None) or (result[0] != "ahid") or (not result[2]):
# 2025-05-29
#    if result[1] == ahid_fph:
#        return result[1] # *primid* serving as an *ahid*
    if (result is None) or (not result[2]):
        return ""
    if (result[0] != "ahid") and (result[1] != ahid_fph):
        return ""

#    print(result[0])
#    print(result[1])
#    print(result[2])

    return result[1] # owner *primid* FPH




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

def authenticate_primid_email(primid_fph, email):
    if not re_email.match(email):
        return False
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT primid_email_1_hash, primid_email_2_hash
            FROM primids
            WHERE entity_fph = ?
            """,
            (primid_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
        if result is None:
            return False
        em1hash = result[0]
        em2hash = result[1]
        if check_auth_hash(email, em1hash):
            return True
        elif check_auth_hash(email, em2hash):
            return True
        else:
            return False

#==============================================================================


def hrns_to_name_and_namespace(hrns):
    if not re_hrns.match(hrns):
        return "", "", "", hrns + " is not an HRNS"
    n = hrns.split(".")
    name = n.pop([0])
    namespace_hrns = ".".join(n)
    namespace_fph, \
    namespace_hrns, \
    etype, \
    m = identify_entity(namespace_hrns)
    if m:
        return "", "", "", m
    if not namespace_fph:
        return "", "", "", hrns + " does not include a valid parent namespace"
    return name, namespace_fph, namespace_hrns


#==============================================================================
## Separate the entity's *name* from the identifier of its parent *namespace*:
#
def split_hrns(identifier_hrns):
    if not re_hrns.match(identifier_hrns):
        return "", ""
    names = identifier_hrns.split(".")
    name = names.pop(0)
    parent_namespace_hrns = ".".join(names).strip(".")
    #print(name + " | " + parent_namespace_hrns)
    return name, parent_namespace_hrns


#==============================================================================


def random_filename():
    return nshash(unixtime_str())





#==============================================================================
