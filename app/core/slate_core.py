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
from app.core.common import ledger_timestamp
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

#from app.core.messaging import send_message

from app.core.regexp_list import re_pvalue

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
    # By default, ownership is inherited from the parent *namespace* but may
    # be overridden.
    #
    # That ownership is not the same as a stewardship. If a *namespace* has an
    # owner it needs no stewards and, if it is an *identity* serving as the
    # root *namespace* of such a tree it cannot have stewards, but *namespaces*
    # created as children/descendants of such a root may have stewards if the
    # owner chooses to invite them.

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # 2025-06-28
        # - Added table to identify types associated with a registered FPH
        #
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS entities_registered (" \
                + "entity_fph TEXT PRIMARY KEY, " \
                + "parent_ns_fph TEXT, " \
                + "namespace INTEGER NOT NULL DEFAULT 0, " \
                + "currency INTEGER NOT NULL DEFAULT 0, " \
                + "account INTEGER NOT NULL DEFAULT 0, " \
                + "primid INTEGER NOT NULL DEFAULT 0, " \
                + "secid INTEGER NOT NULL DEFAULT 0, " \
                + "ahid INTEGER NOT NULL DEFAULT 0" \
            + ");"
        )
        # Create namespaces table:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS namespaces (" \
                + "entity_fph TEXT PRIMARY KEY, " \
                + "active INTEGER NOT NULL DEFAULT 1, " \
                + "stewards_fph_list BLOB, " \
                + "sandbox INTEGER NOT NULL DEFAULT 0, " \
                + "default_currency_fph TEXT DEFAULT '', " \
                + "private INTEGER NOT NULL DEFAULT 0, " \
                + "owner_fph TEXT DEFAULT ''" \
            + ");"
        )

        # NB, since a *primid* or *secid* can serve as the root private
        # *namespace*, a default *currency* must be specified. This has the
        # same identifier as this *primid* initially but may be changed
        # subsequently should the need arise.
        #
        # Since v.0.2, the same identifier can serve for one instance of each
        # of the following entity types:
        #   *primid*    -- a.k.a. *login identity* - unique agent identifier
        #   *ahid*      -- pairing *identity*
        #   *secid*     -- a.k.a. *alias* (hidden in omtrad mode)
        #   *currency*
        #   *namespace*
        #   *account*   -- hidden in omtrad mode
        #
        # Since an identifier is no longer sufficient to specify the type of an
        # entity, stewardship lists are now maintained for *namespaces* and
        # *currencies* separately.
        #
        # Create *primids* table:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS primids (" \
                + "entity_fph TEXT PRIMARY KEY, " \
                + "active INTEGER NOT NULL DEFAULT 1, " \
                + "primid_realname TEXT, " \
                + "primid_email_1_hash TEXT NOT NULL, " \
                + "primid_email_2_hash TEXT, " \
                + "secids_fph_list BLOB, " \
                + "ahids_fph_list BLOB, " \
                + "accounts_fph_list BLOB, " \
                + "pmap BLOB, " \
                + "nstewardships_fph_list BLOB, " \
                + "cstewardships_fph_list BLOB, " \
                + "default_currency_fph TEXT NOT NULL, " \
                + "password_hash BLOB NOT NULL, " \
                + "pin TEXT, " \
                + "access_token_hash BLOB, " \
                + "administrator INTEGER NOT NULL DEFAULT 0" \
            + ");"
        )
        # Create *secids* table:
        #
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS secids (" \
                + "entity_fph TEXT, " \
                + "active INTEGER NOT NULL DEFAULT 1, " \
                + "primid_fph TEXT, " \
                + "accounts_fph_list BLOB" \
            + ");"
        )
        # Create *ahids* (*account-holder identities*) table:
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
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS ahids (" \
                + "entity_fph TEXT, " \
                + "primid_fph TEXT, " \
                + "active INTEGER NOT NULL DEFAULT 1" \
            + ");"
        )
        # Create currencies table:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS currencies (" \
                + "entity_fph TEXT PRIMARY KEY, " \
                + "active INTEGER NOT NULL DEFAULT 1, " \
                + "private INTEGER NOT NULL DEFAULT 0, " \
                + "currency_prefix TEXT, " \
                + "currency_suffix TEXT, " \
                + "default_account_name TEXT DEFAULT 'local', " \
                + "stewards_fph_list BLOB, " \
                + "sandbox INTEGER NOT NULL DEFAULT 0, " \
                + "category TEXT DEFAULT ''" \
            + ");"
        )
        # Create accounts table:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS accounts (" \
                + "entity_fph TEXT PRIMARY KEY, " \
                + "active INTEGER NOT NULL DEFAULT 1, " \
                + "account_owner_fph TEXT NOT NULL, " \
                + "account_ahid_fph TEXT NOT NULL DEFAULT, " \
                + "account_currency_fph TEXT NOT NULL, " \
                + "account_balance INTEGER NOT NULL DEFAULT 0, " \
                + "volume INTEGER NOT NULL DEFAULT 0, " \
                + "type TEXT, " \
                + "vector BLOB, " \
                + "vector_map BLOB, " \
                + "matrix BLOB, " \
                + "matrix_map BLOB, " \
                + "ts_pointer BLOB" \
            + ");"
        )
        # Create currency_accounts table:  ### PROBABLY NOT NEEDED
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS currency_accounts (" \
                + "currency_fph TEXT, " \
                + "account_fph TEXT" \
            + ");"
        )
        # Create login (temporary data) table:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS login (" \
                + "entity_fph TEXT, " \
                + "login_id_fph TEXT, " \
                + "login_authenticated INTEGER NOT NULL DEFAULT 0" \
            + ");"
        )
        conn.commit()
        cursor.close()

#==============================================================================
# A new identifier is registered by
# (1) creation of an FPH>HRNS and HRNS>FPH mapping pair; and
# (2) creation of an entry in the  identifiers_registered  table.

def register_identifier(identifier_hrns):

    if not re_hrns.match(identifier_hrns):
        return ""

    name, parent_ns_hrns = split_hrns(identifier_hrns)

    parent_ns_fph, m = hrns_to_fph(parent_ns_hrns)

    identifier_fph, m = hrns_to_fph(identifier_hrns)
    if m:
        print(m)
        delete_fph_from_map(identifier_fph)
        return ""

    # An entry is created for this FPH in the [entities_registered] table if
    # and only if it dies not exist already.
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            insert_str = "INSERT INTO entities_registered (" \
                       + "entity_fph, " \
                       + "parent_ns_fph, " \
                       + "namespace, " \
                       + "currency, " \
                       + "account, " \
                       + "primid, " \
                       + "secid, " \
                       + "ahid" \
                       + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            # Initially, no entity type is registered for this identifier:
            cursor.execute(
                insert_str, (entity_fph, parent_ns_fph, 0, 0, 0, 0, 0, 0)
            )
            conn.commit()
        cursor.close()

    return identifier_fph


#
def register_identifier_by_name_and_parent_fph(name, parent_ns_fph):
    parent_ns_fph, parent_ns_hrns, etypes, m = identify_entity(parent_ns_fph)
    # NB, an existing entity of any type may be accepted as a parent:
    if not parent_ns_fph:
        return "", "Parent namespace does not exist"
    if not re_name.match(name):
        return "", "Unacceptable name"
    identifier_hrns = name + NS + parent_ns_hrns
    identifier_fph = register_identifier(identifier_hrns)
    return identifier_fph, ""




    identifier_fph, m = hrns_to_fph(identifier_hrns)
    if m:
        print(m)
        delete_fph_from_map(identifier_fph)
        return ""

    # An entry is created for this FPH in the [entities_registered] table if
    # and only if it dies not exist already.
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            insert_str = "INSERT INTO entities_registered (" \
                       + "entity_fph, " \
                       + "parent_ns_fph, " \
                       + "namespace, " \
                       + "currency, " \
                       + "account, " \
                       + "primid, " \
                       + "secid, " \
                       + "ahid" \
                       + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            # Initially, no entity type is registered for this identifier:
            cursor.execute(
                insert_str, (entity_fph, parent_ns_fph, 0, 0, 0, 0, 0, 0)
            )
            conn.commit()
        cursor.close()

    return identifier_fph








#==============================================================================
## Get the list of *entity* types registered for a specified FPH::

def get_entity_types(entity_fph):

    if not re_fph.match(entity_fph):
        return [], "Invalid FPH: " + entity_fph

    #entity_hrns = fph_to_hrns(entity_fph)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT namespace, currency, account, primid, secid, ahid
            FROM entities_registered
            WHERE entity_fph = ?
            """,
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is not None:
        entity_types = []
        if result[0]:
            entity_types.append("namespace")
        if result[1]:
            entity_types.append("currency")
        if result[2]:
            entity_types.append("account")
        if result[3]:
            entity_types.append("primid")
        if result[4]:
            entity_types.append("secid")
        if result[5]:
            entity_types.append("ahid")
        return entity_types, ""
    else:
        return [], "No entities of any type registered for " + entity_fph


#==============================================================================
# Register an *entity* type for a specified identifier FPH:

def register_entity_type(entity_fph, etype):
    if not re_fph.match(entity_fph):
        return "Invalid FPH: " + entity_fph
    vetypes = ["namespace", "currency", "account", "primid", "secid", "ahid"]
    if not (entity_type in vetypes):
        return "Invalid entity type: " + entity_type
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # First check that the [entities_registered] table contains an entry
        # for this FPH.
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            # There is no entry for entity_fph:
            cursor.close()
            return "Identifier " + entity_fph + " is not registered"
        cursor.execute(
            "UPDATE entities_registered SET " + etype + " = 1 " \
            "WHERE entity_fph = ?",
            (entity_fph,)
        )
        conn.commit()
        cursor.close()
    return ""

#
# Record the common properties at the point of an entity's creation:
#def register_entity_type(entity_fph, entity_type):
#    # 2025-06-28:
#    # - entity_type field removed because no longer unique to FPH
#    # - common properties now moved to entities_registered table
#    #
#    vetypes = ["namespace", "currency", "account", "primid", "secid", "ahid"]
#    if not (entity_type in vetypes):
#        return "Invalid entity type: " + entity_type
#    with sqlite3.connect(ENTITIES_DB) as conn:
#        cursor = conn.cursor()
#        # First check that entities_registered table contains an entry for the
#        # FPH
#        cursor.execute(
#            "SELECT * FROM entities_registered WHERE entity_fph = ?",
#            (entity_fph,)
#        )
#        result = cursor.fetchone()
#        if result is None:
#            insert_str = "INSERT INTO entities_registered (" \
#                       + "entity_fph, " + entity_type + ") VALUES (?, ?)"
#            cursor.execute(
#                insert_str, (entity_fph, 1)
#            )
#        else:
#            update_str = "UPDATE entities_registered " \
#                       + "SET " + entity_type + " = 1 WHERE entity_fph = ?"
#            cursor.execute(update_str, (entity_fph,))
#        conn.commit()
#        cursor.close()
#    return


















## Deregister an *entity* type for a specified FPH (probably never needed):

def deregister_entity_type(entity_fph, etype):
    if not re_fph.match(entity_fph):
        return "Invalid FPH: " + entity_fph
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        if result is None:  # There is no entry for entity_fph so there is
            cursor.close()
            return "No type has been registered for " +  entity_fph
        else:
            cursor.execute(
                "UPDATE entities_registered SET " + etype + " = 0 " \
                "WHERE entity_fph = ?",
                (entity_fph,)
            )
            conn.commit()
            cursor.close()
            return ""



#==============================================================================
## Entities may be identified either by HRNS or by FPH. Given that these are
## very different in structure, they may be identified automatically:

def identify_entity(entity_identifier): # HRNS or FPH
    if (entity_identifier is None) or (not isinstance(entity_identifier, str)):
        return "", "", [], ""
    entity_identifier = entity_identifier.strip()
    if entity_identifier == SUBSTRATE_FPH:
        return entity_identifier, "", ["namespace"], ""
    if re_fph.match(entity_identifier): # this is an FPH
        entity_fph = entity_identifier.strip()
        entity_hrns = fph_to_hrns(entity_fph)
        if entity_hrns: # entity mapping exists
            entity_types, m = get_entity_types(entity_fph)
            if m:
                return "", "", [], m
            return entity_fph, entity_hrns, entity_types, ""
        else:
            return "", "", [], "Entity " + entity_fph + " does not exist\n"
    elif re_hrns.match(entity_identifier): # this is an HRNS
        entity_hrns = entity_identifier.strip()
        entity_fph, m = hrns_to_fph(entity_identifier)
        if m:
            return "", "", [], m
        if entity_fph: # entity exists
            entity_types, m = get_entity_types(entity_fph)
            if m:
                return "", "", [], m
            return entity_fph, entity_hrns, entity_types, ""
        else:
            return "", "", [], "Entity " + entity_hrns + " does not exist\n"
    else: # this is not an entity
        return "", "", [], ""

        # NB, if a message is returned here it will cause misdirection in the
        # "/register" endpoint (and possibly others) so for the time being an
        # empty string is returned. This can be addressed later if necessary.

#==============================================================================
# Does an entity of type entity_type exist for identifier entity_id ?

def entity_type_is_registered(entity_id, entity_type):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if entity_fph == "":
        return False
    else:
        return (entity_type in etypes)

# Do all entities of types listed in entity_types exist for identifier
# entity_id ?

def entity_types_are_registered(entity_id, entity_types):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if entity_fph == "":
        return False
    else:
        return set(entity_types) <= set(etypes)

#==============================================================================
## Get namespace owner
#
# Here, a *namespace* may also be a *primid* or *secid*.

def get_private_namespace_details(namespace_identifier):

    namespace_fph, \
    namespace_hrns, \
    etypes, \
    m = identify_entity(namespace_identifier)

    # In order to serve as a private *namespace*, at least one of the entities
    # mapped from this FPH mays have one of the follwing types:
    if len(set(["namespace", "primid", "secid"]) & set(etypes)) > 0:
        return False, "", "Entity cannot be a private namespace"

#    if not (namespace_type in ["namespace", "primid", "secid"]):
#        return False, "", "Entity cannot be a private namespace"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT private, namespace_owner
            FROM entities_registered
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

# 2025-06028: This function hasn't been used anywhere yet so no changes are
# required:
#def set_private_namespace_owner(namespace_identifier, identity_identifier):
#
#    namespace_fph, \
#    namespace_hrns, \
#    etypes, \
#    m = identify_entity(namespace_identifier)
#
#    if not (("primid" in etypes) or ("secid" in etypes)):
##    if (namespace_type != "primid") and (namespace_type != "secid"):
#       return "Entity cannot be a private namespace"
#
#    identity_fph, \
#    identity_hrns, \
#    etypes, \
#    m = identify_entity(identity_identifier)

##    if (identity_type != "primid") and (identity_type != "secid"):
##        return "Entity is not a namespace type"

#    with sqlite3.connect(ENTITIES_DB) as conn:
#        cursor = conn.cursor()
#        cursor.execute(
#            """
#            UPDATE entities_common
#            SET owner_fph = ?
#            WHERE entity_fph = ?
#            """,
#            (identity_fph, namespace_fph)
#        )
#        conn.commit()
#        cursor.close()
#
#    return ""



#==============================================================================
## The entities' common properties are recorded:
#
# The *namespaces", *currencies*, "primids", *secids* and *accounts* all have
# some properties in common, so these are held in a seprate table from those
# used to hold the properties distinct to each entity type.

# 2025-07-10: TO DO:
# Move "private" and "active" flags into the entities specific tables to enable
# these to be set/cleared independently.

# 2025-07-10: The following function replaces the
#   register_entity_type( )
# function.

# Register the entity types associated with a new identifier:
#def register_entity(
#        entity_fph,
#        parent_ns_fph,
#        entity_types # list
#    ):
#    vetypes = ["namespace", "currency", "account", "primid", "secid", "ahid"]
#    vlist = []
#    for etype in vetypes:
#        if etype in entity_types:
#            vlist.append("1")
#        else:
#            vlist.append("0")
#    valuesstr = "(" + ", ".join(vlist) + ")"
#    with sqlite3.connect(ENTITIES_DB) as conn:
#        cursor = conn.cursor()
#        cursor.execute(
#            "INSERT INTO entities_registered (entity_fph, parent_ns_fph, " \
#            + ", ".join(vetypes) + ") VALUES (" + valuesstr + ")",
#            (entity_fph,)
#        )
#        conn.commit()
#        cursor.close()
#    return

#==============================================================================

#def register_entities(
#        entity_fph,
#        parent_ns_fph,
#        *entity_type
#    ):
#    # Any invalid entity types specified will be ignored.
#    etypes = ""
#    valsub = []
#    trues = ""
#    vetypes = ["namespace", "currency", "account", "primid", "secid", "ahid"]
#    for etype in entity_type:
#        if entity_type in vetypes:
#            etypes.append(etype)
#            valsub.append("?")
#            trues.append(1)
#    if len(etypes) == 0:
#        return "No valid entity types were specified"
#    with sqlite3.connect(ENTITIES_DB) as conn:
#        cursor = conn.cursor()
#        # First check that entities_registered table contains an entry for the
# FPH
#        cursor.execute(
#            "SELECT * FROM entities_registered WHERE entity_fph = ?",
#            (entity_fph,)
#        )
#        result = cursor.fetchone()
#        if result is None:
#            insert_str = "INSERT INTO entities_registered (" \
#                       + "entity_fph, parent_ns_fph, " + ", ".join(etypes) \
#                       + ") VALUES (" + ", ".join(valsub) + ")"
#            cursor.execute(
#                insert_str, (entity_fph, parent_ns_fph, ", ".join(trues))
#            )
#        else:
#            update_str = "UPDATE entities_registered SET "
#            etl = []
#            for etype in etypes:
#                etl.append(entity_type + " = 1")
#            update_str += ",".join(etl) + " WHERE entity_fph = ?"
#            cursor.execute(update_str, (entity_fph,))
#        conn.commit()
#        cursor.close()
#    return ""





#==============================================================================
## Get the common properties for this entity identified by FPH or HRNS.
#
# Returns an error message in the event of any problem.

# 2025-06-28:
# - it is now necessary to specify both FPH and entity type

def get_entity_common_properties(entity_id, entity_type): # FPH or HRNS

    entity_fph, \
    entity_hrns, \
    etypes, \
    m = identify_entity(entity_id)
    if m:
        return "", "", m
    if entity_fph == "":
        return "", "", entity_id + " not registered"
    if not entity_type in etypes:
        return "", "", entity_id + " not " + entity_type

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT parent_ns_fph
            FROM entities_registered
            WHERE entity_fph = ?
            """,
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return entity_fph, "", "Not found"

    parent_ns_fph = result[0]
    return entity_fph, parent_ns_fph, ""

#==============================================================================
## Check whether an entity is currently active:

def entity_is_active(entity_id, entity_type):

    entity_fph, \
    entity_hrns, \
    etypes, \
    m = identify_entity(entity_id)
    if m:
        return False, m
    if not (entity_type in etypes):
        return False, entity_id + " is not " + entity_type

    entity_fph, \
    parent_ns_fph, \
    private, \
    active, \
    m = get_entity_common_properties(entity_fph, entity_type)
    return active, m


#==============================================================================
## Check whether a *namespace* is private:

def privacy(entity_id, entity_type): # *namespace*, *primid* or *secid*

    entity_fph, \
    entity_hrns, \
    etypes, \
    m = identify_entity(entity_id)
    if m:
        return False
#    if len(set(["namespace", "primid", "secid"]) & set(etypes)) == 0:
#        return False
    if not (entity_type in ["namespace", "primid", "secid"]):
        return False

    entity_fph, \
    parent_ns_fph, \
    m = get_entity_common_properties(entity_fph, entity_type)
    if m:
        return False
    return private

#==============================================================================
## Get owner of entity:
def get_owner(entity_id, entity_type):

    entity_fph, \
    entity_hrns, \
    etypes, \
    m = identify_entity(entity_id)
    if m:
        return ""
    if not (entity_type in etypes):
        return ""
    if not (entity_type in ["account", "namespace", "primid", "secid"]):
        return ""
    select_str = "SELECT owner_fph FROM " \
               + entity_type + "s WHERE entity_fph = ?"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(select_str, (entity_fph,))
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return ""
    owner_fph = result[0]
    return owner_fph











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
    etypes, \
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
    if not entity_type_is_registered(primid_fph, "primid"):
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
    if not entity_type_is_registered(primid_fph, "primid"):
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
    etypes, \
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
    parent_ns_fph, \
    m = get_entity_common_properties(account_fph, "account")
    if m:
        return False, False, "", "", "", 0, 0, m

    currency_fph, \
    owner_fph, \
    ahid_fph, \
    balance, \
    volume, \
    active, \
    m = get_account_specific_properties(account_fph)
    if m:
        return False, False, "", "", "", 0, 0, m
    if volume is None:
        volume = 0

    return True, active, currency_fph, owner_fph, ahid_fph, balance, volume, ""

#==============================================================================
#

def namespace_status(namespace_fph):

    if not re_fph.match(namespace_fph):
        return "", "", [], "Invalid FPH: " + namespace_fph

    entity_fph, \
    parent_ns_fph, \
    private, \
    active, \
    m = get_entity_common_properties(namespace_fph, "namespace")
    if m:
        return False, False, [], m
#    if entity_type != "namespace":
#        return False, False, [], namespace_fph + " is not a namespace"

    stewards_list, m = list_stewards(namespace_fph, "namespace")
    if m:
        return False, private, False, [], m

    return True, private, active, stewards_list, ""



#==============================================================================
# A new *primid* is created in the specified namespace. This function is used
# only at the point of registration.
#
# When a new *primid* is created, the following additional entities are created
# using the same identifier (HRNS-FPH pair):
# - a *namespace* the initial steward of which is this *primid*
# - a *currency* the initial steward of which is this *primid*
# - an *ahid* the owner of which is this *primid*
# - an *account* (addressed by the pairing of this *currency* and *ahid*) the
#   HRNS of which is not formed in the conventional way (as in the general case
#   where the HRNS of the *currency* and *ahid* are distinct).

def new_primid(
        username,
        parent_ns_fph,
        realname,
        email_address_1,
        email_address_2,
        password,
        pin
    ):

    errors = ""

    if not re_pin.match(pin):
        return "", "", "", "Invalid PIN provided."

    parent_ns_fph, \
    parent_ns_hrns, \
    etypes, \
    m = identify_entity(parent_ns_fph)
    if parent_ns_fph == "":
        return "", "", "", m # parent_ns_fph is invalid

    namespace_hrns = fph_to_hrns(parent_ns_fph)
    primid_hrns = username + NS + namespace_hrns

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

    access_token = generate_access_token()
    access_token_hash = auth_hash(access_token)

    #get_default_currency(entity_identifier)

    # NB, when a new *primid* is created the following additional entities (of
    # which it will be the owner or a steward) are created and registered to
    # the same identifer:
    # - a *namespace* (the root of this *primid*s private *namesapce* tree)
    # - a *currency* (of which this *primid* will be the initial steward)
    # - an *ahid* (since any *primid* must serve also as an *ahid*)
    # - an *account* owned by this *primid*
    # However, a *secid* cannot be created using this identifier.

    # The identifier of any existing entity cannot be used for a new *primid*:
    if entity_type_is_registered(primid_hrns, "primid"):
        return "", "", "", primid_hrns + " exists already (primid)"
    # The identifier can now be registered (creating the HRNS>FPH and FPH>HRNS
    # mappings):
    primid_fph = register_identifier(primid_hrns)
    if not primid_fph: # Unable to register identifier
        return "", "", "", "Unable to register " + primid_hrns

    #stewardships_fph_list = pickle.dumps([])
    secids_fph_list = []
    # This *primid* is the owner of a an *account* having the same FPH:
    accounts_fph_list = [primid_fph]
    # This *primid* is the initial steward of a *namespace* and a *currency*
    # having the same FPH:
    nstewardships_fph_list = [primid_fph]
    cstewardships_fph_list = [primid_fph]
    # POTENTIAL TRAP: This means that whenever either a *namespace* or a
    # *currency* is created, an entity of the other type must be created and
    # registered for the same identifier.

    default_currency_fph = primid_fph

    # First we register a *primid* for this identifier:
    register_entity_type(primid_fph, "primid")

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
                nstewardships_fph_list,
                cstewardships_fph_list,
                default_currency_fph,
                password_hash,
                pin,
                access_token_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                primid_fph,
                realname,
                auth_hash(email_address_1),
                auth_hash(email_address_2),
                pickle.dumps(secids_fph_list),
                pickle.dumps({}),
                pickle.dumps(accounts_fph_list),
                pickle.dumps(nstewardships_fph_list),
                pickle.dumps(cstewardships_fph_list),
                primid_fph, # identifier of default *currency*
                #password_already_hashed,    # restored 2024-11-10 19.50
                auth_hash(password),        # restored 2024-11-10 19.50
                pin,
                auth_hash(access_token),
            )
        )
        conn.commit()
        cursor.close()

    # A new *currency* is registered with the same identifier as the *primid*
    # which also serves as its initial steward.
    currency_fph, \
    currency_hrns, \
    m = new_currency(username, parent_ns_fph, primid_fph, "", "", username)

    # A new *namespace* is created with the same identifier as the *primid*
    # which also serves as its initial steward.
    namespace_fph, \
    namespace_hrns, \
    m = new_namespace(username, parent_ns_fph, currency_fph, primid_fph)

    # A new *ahid* is registered with the same identifier as the *primid*
    register_entity_type(primid_fph, "ahid")

    # A new *account* is created  with the same identifier as the *primid*
    # which also serves as its initial steward.
    account_fph, \
    account_hrns, \
    m = new_account(
            username, parent_ns_fph, primid_fph, primid_fph, currency_fph
        )

    # A new *secid* is created  with the same identifier as the *primid*:

#    secid_fph, secid_hrns, m = new_secid(
#        username,
#        parent_ns_fph,
#        primid_fph
#    )



    return primid_fph, primid_hrns, access_token, m

# Although the initial access token is generated automatically here, it may be
# updated by the primid at any time.

#==============================================================================
## A new *secid* is created:

def new_secid(
        username,
        parent_ns_fph,
        primid_fph
    ):
    if not re_fph.match(parent_ns_fph):
        return "", "", "Invalid parent namespace: " + parent_ns_fph

    parent_ns_hrns = fph_to_hrns(parent_ns_fph)
    secid_hrns = username + "." + parent_ns_hrns

    entity_fph, \
    entity_hrns, \
    etypes, \
    m = identify_entity(secid_hrns)
#    if m:
#        print(m)
    if entity_fph and ("secid" in etypes):
        return "", "", "secid " + secid_hrns + " exists already"

    else:
        secid_fph, m = hrns_to_fph(secid_hrns)
        if m:
            return "", "", m

    m = register_entity_type(secid_fph, "secid")

    # Add the *secid*-specific properties:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO secids (entity_fph, primid_fph, accounts_fph_list) " \
            + "VALUES (?, ?, ?)",
            (secid_fph, primid_fph, pickle.dumps([]))
        )
        cursor.execute(
            "SELECT secids_fph_list FROM primids WHERE entity_fph = ?",
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
            "UPDATE primids SET secids_fph_list = ? WHERE entity_fph = ?",
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

#
#==============================================================================
## A new *ahid* is created:

def new_ahid(
        username,
        parent_ns_fph,
        primid_fph
    ):
    if not re_fph.match(parent_ns_fph):
        return "", "", "Invalid parent namespace: " + parent_ns_fph

    parent_ns_hrns = fph_to_hrns(parent_ns_fph)
    ahid_hrns = username + "." + parent_ns_hrns

    entity_fph, entity_hrns, etypes, m = identify_entity(ahid_hrns)
    if entity_fph:
        if "ahid" in etypes:
            return "", "", "Account-holder " + ahid_hrns + " exists already"
        else:
            register_entity_type(ahid_fph, "secid")
            return entity_fph, entity_hrns, ""
    else:
        ahid_fph, m = hrns_to_fph(ahid_hrns)

    register_entity_type(ahid_fph, "ahid")

    # Add the *secid*-specific properties:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO secids (entity_fph, primid_fph, accounts_fph_list) " \
            + "VALUES (?, ?, ?)",
            (secid_fph, primid_fph, pickle.dumps([]))
        )
        cursor.execute(
            "SELECT secids_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            secids_fph_list = []
        else:
            secids_fph_blob = result[0]
            secids_fph_list = pickle.loads(secids_fph_blob)
        secids_fph_list.append(secid_fph)
        secids_fph_blob = pickle.dumps(secids_fph_list)
        cursor.execute(
            "UPDATE primids SET secids_fph_list = ? WHERE entity_fph = ?",
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
        parent_ns_fph,
        default_currency_fph,
        initial_steward_fph
    ):
    # The substrate is a special case of parent *namespace* (nameless):
    if parent_ns_fph == SUBSTRATE_FPH:
        parent_ns_hrns = ""
        etype = "namespace"
    else:
        parent_ns_fph, \
        parent_ns_hrns, \
        etypes, \
        m = identify_entity(parent_ns_fph)
    if parent_ns_fph == "":
        return "", "", "Parent namespace does not exist"

    if not re_slatename.match(namespace_name):
        return "", "", namespace_name + " is not a valid name"

    if parent_ns_hrns:
        namespace_hrns = namespace_name + "." + parent_ns_hrns
    else:
        namespace_hrns = namespace_name

    existing_namespace_fph, \
    existing_namespace_hrns, \
    etypes, \
    m = identify_entity(namespace_hrns)
#    if existing_namespace_fph:
#        return "", "", "Entity " + namespace_hrns + " is already registered"
    #
    entity_fph, \
    entity_hrns, \
    etypes, \
    m = identify_entity(namespace_hrns)
#    if m:
#        print(m)
    if entity_type_is_registered(entity_fph, "namespace"):
        return "", "", "Namespace " + namespace_hrns + " is already registered"

    # The HRNS and FPH are added to the FPH>HRNS and HRNS>FPH maps:
    namespace_fph, m = hrns_to_fph(namespace_hrns)

    register_entity_type(namespace_fph, "namespace")

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO namespaces (
                entity_fph,
                stewards_fph_list,
                default_currency_fph
            )
            VALUES (?, ?, ?)
            """,
            (   namespace_fph,
                pickle.dumps([initial_steward_fph]),
                default_currency_fph
            )
        )
        conn.commit()
        cursor.close()

    return namespace_fph, namespace_hrns, ""

#==============================================================================
## A new currency is added:

def new_currency(
        currency_name,
        parent_ns_fph,
        initial_steward_fph,
        currency_prefix,
        currency_suffix,
        default_account_name
    ):
    # The initial *account* in this *currency* is assigned to its initial
    # steward (which must exist already).

    parent_ns_fph, \
    parent_ns_hrns, \
    etypes, \
    m = identify_entity(parent_ns_fph)
    if parent_ns_fph == "":
        return "", "", "Parent namespace does not exist"

    if not re_slatename.match(currency_name):
        return "", "", currency_name + " is not a valid name"

    if default_account_name:
        if not re_slatename.match(default_account_name):
            return "", "", default_account_name + " is not a valid name"

    currency_hrns = currency_name + "." + parent_ns_hrns

    entity_fph, \
    entity_hrns, \
    etypes, \
    m = identify_entity(currency_hrns)
#    if m:
#        print(m)
    if entity_type_is_registered(entity_fph, "currency"):
        return "", "", "Currency " + currency_hrns + " is already registered"

    currency_fph, m = hrns_to_fph(currency_hrns)

    register_entity_type(currency_fph, "currency")

    # Now add currency specific properties:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO currencies (entity_fph, currency_prefix, " \
            + "currency_suffix, default_account_name, stewards_fph_list) " \
            + "VALUES (?, ?, ?, ?, ?)",
            (
                currency_fph,
                currency_prefix,
                currency_suffix,
                default_account_name,
                pickle.dumps([initial_steward_fph])
            )
        )
        cursor.execute(
            "SELECT cstewardships_fph_list FROM primids WHERE entity_fph = ?",
            (initial_steward_fph,)
        )
        result = cursor.fetchone()
        if result is not None:
            cstewardships_fph_blob = result[0]
            cstewardships_fph_list = pickle.loads(stewardships_fph_blob)
        else:
            cstewardships_fph_list = []
        if not (currency_fph in stewardships_fph_list):
            cstewardships_fph_list.append(currency_fph)
            cstewardships_fph_blob = pickle.dumps(stewardships_fph_list)
            cursor.execute(
                "UPDATE primids SET cstewardships_fph_list = ? " \
                + "WHERE entity_fph = ?",
                (cstewardships_fph_blob, initial_steward_fph)
            )
            conn.commit()
        cursor.close()

    return currency_fph, currency_hrns, ""

#==============================================================================
## A new account is created in a specified currency:

def new_account(
        account_name,
        parent_ns_fph,
        owner_fph,      # (Owner may be a *primid* or a *secid*)
        ahid_fph,       # *account-holder* for omtrad mode.
        currency_fph
    ):

    if not re_fph.match(parent_ns_fph):
        return "", "", "Invalid parent namespace FPH: " + parent_ns_fph

    if not re_fph.match(owner_fph):
        return "", "", "Invalid owner FPH: " + owner_fph

    parent_ns_hrns = fph_to_hrns(parent_ns_fph)
    account_hrns = account_name + "." + parent_ns_hrns

    owner_fph, \
    owner_hrns, \
    etypes, \
    m = identify_entity(owner_fph)

    if ("primid" in etypes):
        a_table = "primids"
    elif ("secid" in etypes):
        a_table = "secids"
    else:
        return "", "", owner_fph + " is not an agent"

    if not entity_type_is_registered(currency_fph, "currency"):
        return "", "", currency_fph + " is not a currency"

    currency_fph, \
    currency_hrns, \
    active, \
    private, \
    sandbox, \
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
    etypes, \
    m = identify_entity(account_hrns)
#    if m:
#        print(m)
#    if entity_fph:
    if "account" in etypes:
        # an *account* is already registered for this identifier
        return "", "", account_hrns + " exists already"

    account_fph, m = hrns_to_fph(account_hrns)

    register_entity_type(account_fph, "account")

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
    etypes, \
    m = identify_entity(namespace_identifier)
    if m:
        return False, False, False, "", "", [], m
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Add the stewarded entity's FPH to the *primid*'s stewardships list:
        cursor.execute(
            "SELECT active, sandbox, private, owner_fph, stewards_fph_list, " \
            + "default_currency_fph FROM namespaces " \
            + "WHERE entity_fph = ?", (namespace_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        m = "Namespace " + fph_to_hrns(namespace_fph) + " not found"
        return False, False, False, "", "", [], m
    else:
        active = bool(result[0])
        sandbox = bool(result[1])
        private = bool(result[2])
        owner_fph = result[3]
        stewards_fph_blob = result[4]
        currency_fph = result[5]
        stewards_list = pickle.loads(stewards_fph_blob)
    return active, sandbox, private, owner_fph, currency_fph, stewards_list, ""

#==============================================================================
## Set the default *currency* for the *namespace* (including that of a
## *primid-namespace* or *secid-namespace*).

def set_default_currency(entity_identifier, currency_identifier):

    currency_fph, \
    currency_hrns, \
    etypes, \
    m = identify_entity(currency_identifier)
    if m:
        return m
    if not currency_fph:
        return "Currency cannot be identified"

    entity_fph, \
    entity_hrns, \
    etypes, \
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
            UPDATE entities_registered
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

    entity_fph, entity_hrns, etypes, m = identify_entity(entity_identifier)
    if not set(["namespace", "primid", "secid", "currency"]) <= set(etypes):
        return fph_to_hrns(entity_identifier) + " is not a namespace type"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT default_currency_fph
            FROM entities_registered
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
    etypes, \
    m = identify_entity(currency_identifier)
    if m:
        return "", "", False, False, False, "", "", "", [], m

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Add the stewarded entity's FPH to the *primid*'s stewardships list:
        cursor.execute(
            "SELECT active, private, sandbox, " \
            + "currency_prefix, currency_suffix, default_account_name, " \
            + "stewards_fph_list FROM currencies WHERE entity_fph = ?",
            (currency_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        m = "Currency " + fph_to_hrns(currency_fph) + " not found"
        return "", "", False, False, False, "", "", "", [], m
    else:
        active = result[0]
        private = result[1]
        sandbox = result[2]
        prefix = result[3]
        suffix = result[4]
        default_account_name = result[5]
        stewards_fph_blob = result[6]
        stewards_list = pickle.loads(stewards_fph_blob)

        return currency_fph, currency_hrns, active, private, sandbox, \
               prefix, suffix, default_account_name, stewards_list, ""

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

    if entity_type_is_registered(agent_fph, "primid"):
        accounts_fph_list, m = list_primid_accounts(agent_fph)
        if m:
            return [], m
    elif entity_type_is_registered(agent_fph, "secid"):
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
    etypes, \
    m = identify_entity(currency_identifier)
    if not ("currency" in etypes):
        return [], currency_identifier + " is not a currency"

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
    etypes, \
    m = identify_entity(primid_identifier)
    if not ("primid" in etypes):
        return [], primid_identifier + " is not a primid"

    currency_fph, \
    currency_hrns, \
    etypes, \
    m = identify_entity(primid_identifier)
    if not ("currency" in etypes):
        return [], currency_identifier + " is not a currency"

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
    etypes, \
    m = identify_entity(agent_identifier)

    # These are mutually exclusive. A *primid* is sought first and only if
    # not found is a *secid* sought.
    if "primid" in etypes:
        return list_primid_currencies(agent_fph)
    elif "secid" in etypes:
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
                FROM entities_registered
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
                   volume,
                   active
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
        active = bool(result[5])
    else: # no record for account_fph
        return "", "", "", 0, 0, False, "Account not found"

    if not re_fph.match(owner_fph):
        return "", "", "", 0, 0, False, "Invalid owner FPH: " + owner_fph

    if not re_fph.match(currency_fph):
        return "", "", "", 0, 0, False, "Invalid currency FPH: " + currency_fph

    return currency_fph, owner_fph, ahid_fph, balance, volume, active, ""

#------------------------------------------------------------------------------
# Add a stewardship to a *primid* and a steward to a *namespace* or *currency*:

### CHANGE:
#
# Separate the following into two distinct functions:
# i.e.
#   add_namespace_stewardship(entity_fph, steward_fph)
#   add_currency_stewardship(entity_fph, steward_fph)

def add_namespace_stewardship(entity_fph, steward_fph):
    if not re_fph.match(steward_fph):
        return steward_fph + " is not an FPH"

    if not re_fph.match(entity_fph):
        return entity_fph + " is not an FPH"

    if not entity_type_is_registered(steward_fph, "primid"):
        return steward_fph + " is not a primid."

    if not entity_type_is_registered(entity_fph, "namespace"):
        return "namespace not registered for " + entity_fph

    errors = ""

    stewards_select_str = "SELECT stewards_fph_list FROM namespaces " \
                        + "WHERE entity_fph = ?"

    stewards_update_str = "UPDATE namespaces SET stewards_fph_list = ? " \
                        + "WHERE entity_fph = ?"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Add the stewarded entity's FPH to the *primid*'s stewardships list:
        cursor.execute(
            "SELECT nstewardships_fph_list FROM primids WHERE entity_fph = ?",
            (steward_fph,)
        )
        result = cursor.fetchone()
        stewardship_has_been_registered_already = False
        if result is None:
            nstewardships_fph_list = []
        else:
            nstewardships_fph_list = pickle.loads(result[0])
            if entity_fph in nstewardships_fph_list:
                stewardship_has_been_registered_already = True
        nstewardships_fph_list.append(entity_fph)
        nstewardships_fph_blob = pickle.dumps(nstewardships_fph_list)
        cursor.execute(
            "UPDATE primids SET nstewardships_fph_list = ? " \
            + "WHERE entity_fph = ?",
            (nstewardships_fph_blob, steward_fph)
        )

        # Add the steward's FPH to the *namespace*:
        cursor.execute(stewards_select_str, (entity_fph,))
        result = cursor.fetchone()
        if result is None:
            stewards_fph_list = []
        else:
            stewards_fph_list = pickle.loads(result[0])
            if steward_fph in stewards_fph_list:
                if not stewardship_has_been_registered_already:
                    # Remove the inconsistent steward from entity:
                    nstewardships_fph_list.remove(entity_fph)
                    cursor.execute(
                        "UPDATE primids SET nstewardships_fph_list = ? " \
                        + "WHERE entity_fph = ?",
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

#
def add_currency_stewardship(entity_fph, steward_fph):
    if not re_fph.match(steward_fph):
        return steward_fph + " is not an FPH"
    if not re_fph.match(entity_fph):
        return entity_fph + " is not an FPH"
    if not entity_type_is_registered(steward_fph, "primid"):
        return steward_fph + " is not a primid."
    if not entity_type_is_registered(entity_fph, "currency"):
        return "currency not registered for " + entity_fph

    errors = ""

    stewards_select_str = "SELECT stewards_fph_list FROM namespaces " \
                        + "WHERE entity_fph = ?"

    stewards_update_str = "UPDATE namespaces SET stewards_fph_list = ? " \
                        + "WHERE entity_fph = ?"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Add the stewarded entity's FPH to the *primid*'s stewardships list:
        cursor.execute(
            "SELECT cstewardships_fph_list FROM primids WHERE entity_fph = ?",
            (steward_fph,)
        )
        result = cursor.fetchone()
        stewardship_has_been_registered_already = False
        if result is None:
            cstewardships_fph_list = []
        else:
            cstewardships_fph_list = pickle.loads(result[0])
            if entity_fph in cstewardships_fph_list:
                stewardship_has_been_registered_already = True
        cstewardships_fph_list.append(entity_fph)
        cstewardships_fph_blob = pickle.dumps(cstewardships_fph_list)
        cursor.execute(
            "UPDATE primids SET cstewardships_fph_list = ? " \
            + "WHERE entity_fph = ?",
            (cstewardships_fph_blob, steward_fph)
        )

        # Add the steward's FPH to the *namespace*:
        cursor.execute(stewards_select_str, (entity_fph,))
        result = cursor.fetchone()
        if result is None:
            stewards_fph_list = []
        else:
            stewards_fph_list = pickle.loads(result[0])
            if steward_fph in stewards_fph_list:
                if not stewardship_has_been_registered_already:
                    # Remove the inconsistent steward from entity:
                    nstewardships_fph_list.remove(entity_fph)
                    cursor.execute(
                        "UPDATE primids SET cstewardships_fph_list = ? " \
                        + "WHERE entity_fph = ?",
                        (cstewardships_fph_blob, steward_fph)
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







#------------------------------------------------------------------------------
# Remove single stewardship:

# Remove one or more steward(s) from entity:
def remove_stewards(entity_fph, *primids_fph):
    errors = ""
    #
    if entity_type_is_registered(entity_fph, "namespace"):
        table = "namespaces"
    elif entity_type_is_registered(entity_fph, "currency"):
        table = "currencies"
    else:
        return entity_fph + " is not a stewarded type.\n"

    # Get a list of the entity's current stewards and extend it with any valid
    # primid FPH given:
    stewards_fph_list, m = list_stewards(entity_fph)
    if m:
        errors += m + "\n"
    any_primid_valid = False # flag
    for steward_fph in stewards_fph_list:
        if entity_type_is_registered(steward_fph, "primid"):
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
    etypes, \
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
    etypes, \
    m = identify_entity(removing_steward_id)
    if m:
        return m
    if removing_steward_fph == "":
        return "Removing steward does not exist"

    removed_steward_fph, \
    removed_steward_hrns, \
    etypes, \
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

    if entity_type_is_registered(entity_fph ,"namespace"):
        table = " namespaces "
    elif entity_type_is_registered(entity_fph ,"currency"):
        table = " currencies "
    else:
        return [], entity_fph + " is not a stewarded type"

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
# List *namespace* stewardships of a *primid*:

def list_namespace_stewardships(primid_fph):

    if not re_fph.match(primid_fph):
        return [], primid_fph + " is not an FPH"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT nstewardships_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        nstewardships_fph_list = []
        nstewardships_fph_blob = pickle.dumps(nstewardships_fph_list)
        cursor.execute(
            "UPDATE primids SET nstewardships_fph_list = ? " \
            + "WHERE entity_fph = ?",
            (nstewardships_fph_blob, primid_fph)
        )
        conn.commit()
        cursor.close()
        return [], "Primid " + primid_fph + " has no namespace stewardships."
    else:
        cursor.close()
        nstewardships_fph_blob = result[0]
        nstewardships_fph_list = pickle.loads(nstewardships_fph_blob)
        nstewardships = []
        for nstewardhip_fph in nstewardships_fph_list:
            nstewardships.append(nstewardhip_fph)
    return nstewardships, ""

#------------------------------------------------------------------------------
# List *currency* stewardships of a *primid*:

def list_currency_stewardships(primid_fph):

    if not re_fph.match(primid_fph):
        return [], primid_fph + " is not an FPH"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT cstewardships_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        cstewardships_fph_list = []
        cstewardships_fph_blob = pickle.dumps(cstewardships_fph_list)
        cursor.execute(
            "UPDATE primids SET cstewardships_fph_list = ? " \
            + "WHERE entity_fph = ?",
            (cstewardships_fph_blob, primid_fph)
        )
        conn.commit()
        cursor.close()
        return [], "Primid " + primid_fph + " has no currency stewardships."
    else:
        cursor.close()
        cstewardships_fph_blob = result[0]
        cstewardships_fph_list = pickle.loads(cstewardships_fph_blob)
        cstewardships = []
        for cstewardhip_fph in cstewardships_fph_list:
            cstewardships.append(cstewardhip_fph)
    return cstewardships, ""

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
        etypes, \
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
        #    FROM entities_registered
        #    WHERE entity_type = 'namespace'
        #    AND active = 1;
        #    """
        #)
        cursor.execute(
            """
            SELECT entity_fph
            FROM entities_registered
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
    etypes, \
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
    print("get_ahid_primid( ) called")
    # (1) Each *ahid* belongs to one *primid*
    # (2) Each *primid* may have any number of *ahid*
    # (3) A *primid* may belong to itself as an *ahid*
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_hrns)
    print("etypes: ", end="")
    print(etypes)
    if not ahid_fph:
        print("Zeppo")
        return ""
    if not ("ahid" in etypes):
        print("ahid_fph = " + ahid_fph)
        print("etypes = ", end="")
        print(etypes)
        return ""
    print("Groucho")
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT primid_fph FROM ahids WHERE entity_fph = ?",
            (ahid_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    print("Chico")
    if result is None:
        return ""
    print("Harpo")
    owner_fph = result[0]
    return owner_fph # owner *primid* FPH




#==============================================================================
# List *primid*s:

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
                "SELECT active FROM entities_registered WHERE entity_fph = ?",
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
    etypes, \
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
    #names = identifier_hrns.split(".")
    names = identifier_hrns.split(NS)
    name = names.pop(0)
    #parent_ns_hrns = ".".join(names).strip(".")
    parent_ns_hrns = NS.join(names).strip(NS)
    #print(name + " | " + parent_ns_hrns)
    return name, parent_ns_hrns


#==============================================================================


def random_filename():
    return nshash(unixtime_str())





#==============================================================================

# This file contains functions to emulate the "traditional" OM mode pairing a
# re-useable *ahid* identifier with a *currency* identifier.
#
# On the surface, the bahaviour is a little different from that of the
# SLATE/NESTS approach in that the *account* created to represent the pairing
# is only ever identified (to most users in "omtrad" mode) indirectly by
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

#import sqlite3
#import random
#import os
#import pickle

#from app.core.regexp_list import re_hrns, re_fph

#from app.core.slate_core import hrns_to_fph, fph_to_hrns
#from app.core.slate_core import register_entity_type
#from app.core.slate_core import new_account
#from app.core.slate_core import account_status
#from app.core.slate_core import new_namespace
#from app.core.slate_core import new_primid
#from app.core.slate_core import new_currency
#from app.core.slate_core import identify_entity
#from app.core.slate_core import split_hrns
#from app.core.slate_core import get_currency_specific_properties
#from app.core.slate_core import get_ahid_primid

#from app.core.common import ledger_timestamp

#from app.core.messaging import send_message

#from app.core.regexp_list import re_pvalue

#from app.core.constants import ENTITIES_DB
#from app.core.constants import PAYMENTS_DB

#=============================================================================

# The is a temporary fudge ...

def is_ancestor(entity_hrns, ancestor_id):
    # This version works only within the same constraints as "omtrad" mode
    # (i.e. UTF-8 Latin character set for HRNS).
    ancestor_fph, ancestor_hrns, etype, m = identify_entity(ancestor_id)
    a = ancestor_hrns.split(".")
    e = entity_hrns.split(".")
    is_an_ancestor = True
    while len(a) > 0:
#        e_ = e.pop()
#        a_ = a.pop()
#        if e_ != a_:
        if e.pop() != a.pop():
            is_an_ancestor = False
            break
    return is_an_ancestor

# ... used here primarily to determine whether the parent *namespace* for new
# entities is the private *namespace* of the importing *primid".

def is_in_private_namespace(entity_hrns, pn_id):
    pn_fph, pn_hrns, etype, m = identify_entity(pn_id)
    return is_ancestor(entity_hrns, pn_hrns) or (entity_hrns == pn_hrns)



#=============================================================================

def retrieve_pmap(owner_identifier):

    owner_fph, \
    owner_hrns, \
    etypes, \
    m = identify_entity(owner_identifier)
    if not owner_fph:
        print(owner_fph + " is not registered")
        return {}, owner_identifier + " is not registered"
    if not ("primid" in etypes):
        print(owner_identifier + " is not a primid")
        return {}, owner_identifier + " is not a primid"
    print("pmap owner: " + owner_fph + " > " + owner_hrns)

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
        print("No pmap for " + owner_hrns + " (a)")
        return {}, ""
    elif isinstance(result, tuple) and (result[0] is None):
        print("No pmap for " + owner_hrns + " (b)")
        return {}, ""
    else:
        pmap = pickle.loads(result[0])
        print("pmap for " + owner_hrns + " :")
        print(pmap)
        return pmap, ""     # dictionary of  ahid_hrns:currency_hrns
                            # pairs for display in table.

#=============================================================================

def create_new_pairing(
        owner_identifier,   # *primid* HRNS or FPH
        ahid_hrns,          # HRNS
        currency_hrns       # HRNS
    ):

    # The *currency* and owner *primid* are validated before proceeding to
    # create a new *account-holder*. Only if both exist will a new *account*
    # or *account-holder* be created.

    c_fph, c_hrns, cetypes, m = identify_entity(currency_hrns)
    if not ("currency" in cetypes):
        #print(currency_hrns + " is not a currency")
        return "", currency_hrns + " is not a currency"

    owner_fph, owner_hrns, petypes, m = identify_entity(owner_identifier)
    if not ("primid" in petypes):
        return "", owner_identifier + " is not a primid"

    # If the *ahid* does not exist already it must be created:
    #
    ahid_fph, ahid_hrns_, etypes, m = identify_entity(ahid_hrns)
    if ahid_fph == "": # does not exist
        ahid_name, parent_hrns_ = split_hrns(ahid_hrns)
        parent_fph, parent_hrns, etypes, m = identify_entity(parent_hrns_)

        # The *ahid* is added to the HRNS>FPH and FPH>HRNS maps:
        ahid_fph, m = hrns_to_fph(ahid_hrns)

        # The *ahid* is then added to the entities_registered table.
        register_entity_type(ahid_fph, "ahid")
        with sqlite3.connect(ENTITIES_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ahids " \
                + "(entity_fph, primid_fph, active) " \
                + "VALUES (?, ?, ?)",
                (ahid_fph, owner_fph, 1)
            )
            conn.commit()
            cursor.close()

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
            ahid_fph,
            c_fph
        )

    # The *ahid* may be paired with any *currency* (once only). These
    # serve as the co-ordinates in a grid identifying the *account* created
    # above.
    #
    # If a *pairing* entity does not exist already it is created.
    #
    # The pairings dictionary is retrieved:
    pmap, m = retrieve_pmap(owner_fph)

    if pmap is None:
        pmap = {}

    #if not (ahid_hrns in pmap):
    if not (ahid_hrns in pmap.keys()):
        #print(ahid_hrns + " not in pmap")
        pmap[ahid_hrns] = {}
    if not (currency_hrns in pmap[ahid_hrns].keys()):
        pmap[ahid_hrns][currency_hrns] = account_fph

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Update the pmap:
        cursor.execute(
            "UPDATE primids SET pmap = ? WHERE entity_fph = ?",
            (pickle.dumps(pmap), owner_fph)
        )
        # Update the *ahid*s list:
        cursor.execute(
            "SELECT ahids_fph_list FROM primids WHERE entity_fph = ?",
            (owner_fph,)
        )
        result = cursor.fetchone()
        if (result is None) or (result[0] is None):
            ahids_fph_list = []
        else:
            ahids_fph_list = pickle.loads(result[0])
        ahids_fph_list.append(ahid_fph)
        cursor.execute(
            "UPDATE primids SET ahids_fph_list = ? WHERE entity_fph = ?",
            (pickle.dumps(ahids_fph_list), owner_fph)
        )
        conn.commit()
        cursor.close()

    return account_fph

#=============================================================================




#=============================================================================

def list_primid_ahids(primid_fph):





    return ahids_list





#=============================================================================

def retrieve_pairing_account_fph(ahid_hrns, currency_identifier):

    if not re_hrns.match(ahid_hrns):
        return "", "", ahid_hrns + " is not an account-holder"

    currency_fph, \
    currency_hrns, \
    etypes, \
    m = identify_entity(currency_identifier)
    if not currency_fph:
        print(currency_identifier + " is unidentifiable")
        return "", "", currency_identifier + " is unidentifiable"
    if not ("currency" in etypes):
        print("etypes = ", end="")
        print(etypes)
        return "", "", currency_fph + " is not a currency"


    primid_fph = get_ahid_primid(ahid_hrns)
    if primid_fph:
        #pmap = get_ahid_pmap(primid_fph)
        print("primid = " + primid_fph)
        pmap, m = retrieve_pmap(primid_fph)
    else:
        return "", "", "Unable to retrieve pmap for ahid " + ahid_hrns

    if not (ahid_hrns in pmap.keys()):
        return "", "", ahid_hrns + " is not an account-holder"

    currencies_available = pmap[ahid_hrns]
    #print(currencies_available.keys())
    #if not (currency_hrns in currencies_available.keys()):
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
    m = get_currency_specific_properties(currency_hrns)

    if m:
        print("Groucho")
        print(m)

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








def make_om_payment(
        payer_ahid_hrns,
        payee_ahid_hrns,
        currency_hrns,
        amount,
        annotation
    ):


    return status, m


#==============================================================================
# If the parent *namespace* specified for a new entity is incomplete, the
# missing intermediate *namespace* must be created (and assigned the importing
# *primid* as their initial steward).

def complete_parent_namespace(identifier_hrns, primid_fph):
    if primid_fph == "":
        s_fph, m = hrns_to_fph("adm.cc")
    else:
        s_fph, s_hrns, etype, m = identify_entity(primid_fph)
    c_fph, m = hrns_to_fph("cc")
    entity_fph, entity_hrns, etype, m = identify_entity(identifier_hrns)
    if entity_fph: # the entity exists already
        return entity_fph
    if not re_hrns.match(identifier_hrns):
        return ""
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

#==============================================================================



def create_import_currency(currency_hrns, steward_fph):
    if not re_hrns.match(currency_hrns):
        return "", "", currency_hrns + " is invalid HRNS"
    steward_fph, m = hrns_to_fph("adm.cc")
    currency_fph, currency_hrns, etype, m = identify_entity(currency_hrns)
    if currency_fph: # the entity exists already
        return currency_fph, currency_hrns, currency_hrns + " exists already"
    name, parent_hrns = split_hrns(currency_hrns)
    parent_fph = complete_parent_namespace(parent_hrns)
    currency_fph, \
    currency_hrns, \
    m = new_currency(
            name,
            parent_fph,
            steward_fph,
            "",
            "",
            name
        )
    return currency_fph, currency_hrns, ""








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

def import_csv_dataset(fpath, primid_identifier):
#def import_csv_dataset(fpath, primid_identifier, SC=","):

    # The uploaded file will have been given a randomly generated name and is
    # identified as fpath. The file will be deleted as soon as it has been
    # fully processed.
    #
    # The separator-characted (SC) may be a comma, colon, semicolon or tab, but
    # the default is a comma.
    #
    # If any *currency* specified does not exist it will be created with the
    # uploading agent as its initial steward.
    #
    # If any *ahid* does not exist, it will be created and assigned to the
    # uploading agent.
    #
    # If any ancestor *namespace* does not exist it will be created with the
    # uploading agent as its initial steward.
    #
    # Any identifier imported here will be prefixed to the *primid* HRNS (i.e.
    # located within that *primid*'s private namesapce) unless prefixed with an
    # "@" character.

    primid_fph, primid_hrns, etype, m = identify_entity(primid_identifier)

    report = ["New entities created:"] # a report of new entities created
    errors = [] # a list of errors returned

    with open(fpath, "r") as csv_f:
        rows = csv_f.readlines()

    # Identify separator character from first row of the CSV file:
    #tries_left = 4
    tries = 0
    row0 = rows[0].strip()
    for c in [",", ":", ";", "\t"]:
        field = row0.split(c)
        if len(field) == 5:
            SC = c
            break
    #print("SC = " + c)

    row_count = 0
    for row in rows:
        row_count += 1
        field = row.split(SC)
        if len(field) != 5:
            errors.append("Row " + str(row_count) + ": Wrong number of fields")
            return report, errors
        currency_hrns_ = field[0].strip("\"")
        payer_ahid_hrns = field[1].strip("\"") + "." + primid_hrns
        payee_ahid_hrns = field[2].strip("\"") + "." + primid_hrns
        amount = int(100*float(field[3].strip("\"")))
        annotation = field[4].strip()

        if currency_hrns_[0] == "@": # absolute identifier path
            currency_hrns_ = currency_hrns_.lstrip("@")
        else: # relative identifier path
            currency_hrns_ = currency_hrns_ + "." + primid_hrns

#        if payer_hrns[0] == "@": # absolute identifier path
#            payer_hrns.lstrip("@")
#        else: # relative identifier path
#            payer_hrns = primid_hrns + "." + payer_hrns
#
#        if payee_hrns[0] == "@": # absolute identifier path
#            payee_hrns.lstrip("@")
#        else: # relative identifier path
#            payee_hrns = primid_hrns + "." + payee_hrns

        # Create any missing *currency*:
        currency_fph, currency_hrns, etype, m = identify_entity(currency_hrns_)
        if etype and (etype != "currency"):
            errors.append(currency_hrns + " is " + etype + " not currency")
        if currency_fph == "": # does not exist
            currency_name, parent_hrns = split_hrns(currency_hrns_)
            currency_fph, \
            currency_hrns, \
            m = new_currency(
                    currency_name,
                    complete_parent_namespace(parent_hrns, primid_fph),
                    primid_fph,
                    "",
                    "",
                    currency_name # is used for default *account* name
                )
        pmap, m = retrieve_pmap(primid_fph)

        # Create any missing payer *ahid* and *ahid*|*currency* pairings.
        payer_ahid_name, parent_hrns = split_hrns(payer_ahid_hrns)
        parent_fph = complete_parent_namespace(parent_hrns, primid_fph)
        payer_account_fph = create_new_pairing(
                                primid_hrns,
                                payer_ahid_hrns,
                                currency_hrns
                            )
        if payer_account_fph:
            report.append(payer_ahid_hrns + " created")
            report.append(fph_to_hrns(payer_account_fph) + " created")

        pmap, m = retrieve_pmap(primid_fph)

        # Create any missing payee *ahid* and *ahid*-*currency* pairings.
        payee_ahid_name, parent_hrns = split_hrns(payee_ahid_hrns)
        parent_fph = complete_parent_namespace(parent_hrns, primid_fph)
        payee_account_fph = create_new_pairing(
                                primid_fph,
                                payee_ahid_hrns,
                                currency_hrns
                            )
        if payee_account_fph:
            report.append(payee_ahid_hrns + " created")
            report.append(fph_to_hrns(payee_account_fph) + " created")

        pmap, m = retrieve_pmap(primid_fph)

        m = ah_payment(
                payer_ahid_hrns,
                payee_ahid_hrns,
                currency_hrns,
                amount,
                annotation
            )
        if m:
            errors.append(m)

    return report, errors

#==============================================================================
