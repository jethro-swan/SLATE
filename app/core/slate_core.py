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
from app.core.constants import NSS # NamseSpace Separator character

from app.core.common import filename_timestamp as timestamp
from app.core.common import ledger_timestamp
from app.core.common import nshash
from app.core.common import unixtime_str
#from app.core.payments import ah_payment


#from app.core.messaging import send_message

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from app.core.fph_hrns_maps import delete_fph_from_map
from app.core.fph_hrns_maps import get_parent
from app.core.fph_hrns_maps import record_parent

from app.core.dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from app.core.dbm_functions import dbm_create_map

from app.core.auth import auth_hash, check_auth_hash, generate_access_token

from app.core.regexp_list import *

from app.core.unix_functions import fcopy

from app.core.cctld_list import *

#from app.core.regexp_list import re_pvalue
#from app.core.regexp_list import re_pairaccountname

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
            "CREATE TABLE IF NOT EXISTS hub (" \
            + "hub_id INTEGER PRIMARY KEY AUTOINCREMENT, " \
            + "subdomain TEXT DEFAULT '', " \
            + "must_be_archived INTEGER NOT NULL DEFAULT 1, " \
            + "administrators_fph_list BLOB, " \
            + "single_hub INTEGER NOT NULL DEFAULT 1, " \
            + "hub_members BLOB, " \
            + "synchronized_hubs BLOB, " \
            + "nests_extensions_enabled INTEGER NOT NULL DEFAULT 0, " \
            + "location_details BLOB, " \
            + "contact_details BLOB" \
            + ");"
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
        r = row.split()
        config[r[0]] = r[1]
    return config

#==============================================================================
# Global data, flags, etc.









#==============================================================================
## Create the SQLite entities database

# 2025-08-30: Extending to allow creation od a new entities database file for
# each private *namespace* using the owner's FPH as its filename.

#def create_entities_db():
#
#    if os.path.exists(ENTITIES_DB):
#        # If the database exists already, it is deleted after a time-stamped
#        # copy has been saved.
#        fcopy(ENTITIES_DB, DB_BKP_DIR + '/entities_' + timestamp() + '.db')
#        os.remove(ENTITIES_DB)

def create_entities_db(*owner_fph):

    # Added 2025-08-30:

    # The owner of any private *namespace*
#    if owner_fph is not None:


    if os.path.exists(ENTITIES_DB):
        # If the database exists already, it is deleted after a time-stamped
        # copy has been saved.
        fcopy(ENTITIES_DB, DB_BKP_DIR + '/entities_' + timestamp() + '.db')
        os.remove(ENTITIES_DB)

    # If this entity is a *private namespace* (one that has ramified from a
    # *primid* or *secid*, both that privacy and its ownerhip must be evident.
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
            + "parent_fph TEXT, " \
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
            + "pmap BLOB, " \
            + "nstewardships_fph_list BLOB, " \
            + "cstewardships_fph_list BLOB, " \
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
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS ahids (" \
            + "entity_fph TEXT, " \
            + "primid_fph TEXT, " \
            + "accounts_fph_list BLOB, " \
            + "active INTEGER NOT NULL DEFAULT 1" \
            + ");"
        )
        # Create currencies table:
        #
        # Please note:
        #
        # The "units" field (where used) indicates measure/value/quantity, and
        # must be consistent with the "dimensions" field (if used). The
        # following list of possibilities for each category is far from
        # complete:
        #   - "utime" and "htime":  e.g. years, days, hours, seconds, ...
        #   - "energy":             e.g. kWh, Joules, GeV, ...
        #   - "power":              e.g. W, J/s, etc.
        #   - "force":              e.g. Newton
        #   - "length":             e.g. m, light-years,
        #   - "lte":                e.g. Euro, Pound, Yen, Dollar, ...
        #
        # The "dimensions" field (if used) must be consistent with the "units"
        # field (if used) and vice versa:
        #   - "utime":              T
        #   - "energy":             ML^2T^-2
        #   - "power":              ML^2T^-1
        #   - "length":             L
        #   - "mass":               M
        #   - "speed" | "velocity": LT^-1
        #   - "acceleration":       LT^-2
        #
        # Where "type" is "money", the "metrical_equivalence" field (if used)
        # indicated the legal tender currency for which this substitutes.
        #
        # The "prefix" or "suffix" field (where used) must be consistent with
        # the "units" (if used) and vice versa.
        #
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
            + "type TEXT DEFAULT '', " \
            + "category TEXT DEFAULT '', " \
            + "units TEXT DEFAULT '', " \
            + "metrical_equivalence '', " \
            + "dimensions TEXT DEFAULT ''" \
            + ");"
        )
        # Create accounts table:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS accounts (" \
            + "entity_fph TEXT PRIMARY KEY, " \
            + "active INTEGER NOT NULL DEFAULT 1, " \
            + "account_owner_fph TEXT NOT NULL, " \
            + "account_currency_fph TEXT NOT NULL DEFAULT '', " \
            + "balance INTEGER NOT NULL DEFAULT 0, " \
            + "volume INTEGER NOT NULL DEFAULT 0, " \
            + "account_type TEXT DEFAULT 'money', " \
            + "category TEXT DEFAULT '', " \
            + "units TEXT DEFAULT '', " \
            + "metrical_equivalence '', " \
            + "dimensions TEXT DEFAULT '', " \
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

    # Added 2025-08-30:


#==============================================================================
# A new identifier is registered by
# (1) creation of an FPH>HRNS and HRNS>FPH mapping pair; and
# (2) creation of an entry in the  identifiers_registered  table.

def register_identifier(identifier_hrns):
    if not re_hrns.match(identifier_hrns):
        return ""
    name, parent_hrns = split_hrns(identifier_hrns)
    parent_fph, m = hrns_to_fph(parent_hrns)
    identifier_fph, m = hrns_to_fph(identifier_hrns)
    if m:
        delete_fph_from_map(identifier_fph)
        return ""

    # The parent FPH is registered in the child.parent map:
    if not record_parent(identifier_fph, parent_fph):
        return ""

    # An entry is created for this FPH in the [entities_registered] table if
    # and only if it does not exist already.
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (identifier_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            insert_str = "INSERT INTO entities_registered (" \
                       + "entity_fph, " \
                       + "parent_fph, " \
                       + "namespace, " \
                       + "currency, " \
                       + "account, " \
                       + "primid, " \
                       + "secid, " \
                       + "ahid" \
                       + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
            # Initially, no entity type is registered for this identifier:
            cursor.execute(
                insert_str, (identifier_fph, parent_fph, 0, 0, 0, 0, 0, 0)
            )
            conn.commit()
        cursor.close()

#    print("-"*160)
    id_fph,  id_hrns, etypes, m = identify_entity(identifier_fph)
#    print("New identifier registered: " + identifier_fph)
#    print("id_fph = " + id_fph)
#    print("id_hrns = " + id_hrns)
#    print("etypes = ", end="")
#    print(etypes)
#    print("-"*160)

    return identifier_fph

#==============================================================================
## Is the identifier registered?

def identifier_unregistered(identifier_id):
    if re_hrns.match(identifier_id):
        # nshash( ) is used here because using  hrns_to_fph( ) would add to the
        # HRNS>FPH and FPH>HRNS maps.
        identifier_fph = nshash(identifier_id)
    elif re_fph.match(identifier_fph):
        identifier_fph = identifier_id
    else:
        return True
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (identifier_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        return True
    else:
        return False

#==============================================================================
# The following provides an intermediate bridge to older versions of some
# entity creation functions. It will probably be abandoned soon.

def register_identifier_by_name_and_parent_fph(name, parent_fph):
    parent_fph, parent_hrns, etypes, m = identify_entity(parent_fph)
    # NB, an existing entity of any type may be accepted as a parent:
    if not parent_fph:
        return "", "Parent namespace does not exist"
    if not re_name.match(name):
        return "", "Unacceptable name"
    identifier_hrns = name + NSS + parent_hrns
#    print("identifier_hrns 2 = " + identifier_hrns)
    return register_identifier(identifier_hrns)
    return identifier_fph, ""

#==============================================================================
## Get the list of *entity* types registered for a specified FPH::

def get_entity_types(entity_fph):
    if not re_fph.match(entity_fph):
        return [], "Invalid FPH: " + entity_fph
    entity_hrns = fph_to_hrns(entity_fph)
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT " \
            + "namespace, " \
            + "currency, " \
            + "account, " \
            + "primid, " \
            + "secid, " \
            + "ahid " \
            + "FROM entities_registered " \
            + "WHERE entity_fph = ?",
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
        return [], "No entities registered for " + entity_fph















#==============================================================================
# Set, register or deregister an *entity* type for a specified identifier FPH:

def set_entity_type(identifier_fph, entity_type, value):
    if not re_fph.match(identifier_fph):
        return "Invalid FPH: " + identifier_fph
    # The valid entity types are:
    vetypes = ["namespace", "currency", "account", "primid", "secid", "ahid"]
    if not (entity_type in vetypes):
        return "Invalid entity type: " + entity_type
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Does [entities_registered] table contain an entry for this FPH?
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (identifier_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            cursor.close()
            return "Identifier " + identifier_fph + " is not registered"
        u = "UPDATE entities_registered SET " + entity_type + " = ? " \
            + "WHERE entity_fph = ?"
        cursor.execute(
            u, (int(value), identifier_fph)
        )
        conn.commit()
        cursor.close()
    return ""

def register_full_entity_set(identifier_fph):
    if not re_fph.match(identifier_fph):
        return "Invalid FPH: " + identifier_fph
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Does [entities_registered] table contain an entry for this FPH?
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (identifier_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            cursor.close()
            return "Identifier " + identifier_fph + " is not registered"
        u = "UPDATE entities_registered SET " \
          + "namespace = 1, " \
          + "currency = 1, " \
          + "account = 1, " \
          + "primid = 1, " \
          + "secid = 1, " \
          + "ahid = 1 " \
          + "WHERE entity_fph = ?"
        cursor.execute(u, (identifier_fph,))
        conn.commit()
        cursor.close()
    return ""

def register_primid_entity_set(identifier_fph):
    # This is used when registerind a new *primid*:
    if not re_fph.match(identifier_fph):
        return "Invalid FPH: " + identifier_fph
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Does [entities_registered] table contain an entry for this FPH?
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (identifier_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            cursor.close()
            return "Identifier " + identifier_fph + " is not registered"
        u = "UPDATE entities_registered SET " \
          + "namespace = 1, " \
          + "currency = 1, " \
          + "account = 1, " \
          + "primid = 1, " \
          + "ahid = 1 " \
          + "WHERE entity_fph = ?"
        cursor.execute(
            u, (identifier_fph,)
        )
        conn.commit()
        cursor.close()
    return ""

def register_general_entity_set(identifier_fph):
    # This is used when creating a new *namespace* or *currency*
    if not re_fph.match(identifier_fph):
        return "Invalid FPH: " + identifier_fph
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Does [entities_registered] table contain an entry for this FPH?
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (identifier_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            cursor.close()
            return "Identifier " + identifier_fph + " is not registered"
        u = "UPDATE entities_registered SET " \
          + "namespace = 1, " \
          + "currency = 1 " \
          + "WHERE entity_fph = ?"
        cursor.execute(u, (identifier_fph,))
        conn.commit()
        cursor.close()
    return ""




def register_entity_type(identifier_fph, entity_type):
    return set_entity_type(identifier_fph, entity_type, True)

def deregister_entity_type(identifier_fph, entity_type):
    return set_entity_type(identifier_fph, entity_type, False)

#==============================================================================
## Entities may be identified either by HRNS or by FPH. Given that these are
## very different in structure, they may be identified automatically:

def identify_entity(entity_id): # HRNS or FPH
    if (entity_id is None) or (not isinstance(entity_id, str)):
        return "", "", [], "Invalid identifier"
    entity_id = entity_id.strip()
#    print("(1) entity_id = " + entity_id)
    if entity_id == SUBSTRATE_FPH: # unique exception
        #print("substrate")
        return entity_id, "", list("namespace",), ""
    if re_fph.match(entity_id): # this is an FPH string?
#        print(entity_id + " is an FPH")
        entity_fph = entity_id
        entity_hrns = fph_to_hrns(entity_fph)
        if entity_hrns: # this entity mapping exists
            entity_types, m = get_entity_types(entity_fph)
            if m: # something wrong here
                return "", "", [], m
            return entity_fph, entity_hrns, entity_types, "" # expected result
        else:
            return "", "", [], "Entity " + entity_fph + " does not exist\n"
    elif re_hrns.match(entity_id): # this is an HRNS string?
#        print(entity_id + " is an HRNS")
        entity_hrns = entity_id
        entity_fph, m = hrns_to_fph(entity_id)
        if m: # something wrong here
#            print("something wrong here")
            return "", "", [], m
        if entity_fph: # entity exists
            #print("entity_fph = " + entity_fph)
            entity_types, m = get_entity_types(entity_fph)
            if m:
                #print("m3: " + m)
                #print("Anya")
                return "", "", [], m
            return entity_fph, entity_hrns, entity_types, "" # expected result
        else:
            return "", "", [], "Entity " + entity_hrns + " does not exist\n"
    else: # this is not an entity
        return "", "", [], ""   # NB, if a message is returned here it will
                                #     cause misdirection in the "/register"
                                #     endpoint (and possibly others) so for the
                                #     time being an empty string is returned.
                                #     This can be addressed later if necessary.


#==============================================================================
## Get the FPH of the parent:

def get_parent_fph(entity_id):
    entity_fph, entity_hrns, entity_types, m = dentify_entity(entity_id)
    if not entity_fph:
        return ""
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT parent_fph FROM entities_registered " \
            + "WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        return ""
    return result[0]

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
## Get *namespace* owner
#
# Here, the identifier of the private *namespace* may be that of a *primid*, a
# *secid* or an *ahid*. Where these all share the same identifier, this will be
# the same private *namespace*.

def get_namespace_details(namespace_id):
    namespace_fph, namespace_hrns, etypes, m = identify_entity(namespace_id)
    # Is a *namespace* registered for this identifier?
    if not ("namespace" in etypes):
        return False, "", "Entity is not a namespace"
    # Is at least one of the following types registered for this identifier?
    if not (len(set(["primid", "secid", "ahid"]) & set(etypes)) > 0):
        return False, "", "Entity cannot be a private namespace"
    # Every identifier of a *primid* also identifies an *ahid*, but:
    # (1) the identifier of any *ahid* other than one created alongside a
    #     *primid* cannot be used to identify a different *primid*
    #     subsequently; and
    # (2) the identifier of any *secid* cannot be used subsequently for a new
    #     *primid*.
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT " \
            + "active, " \
            + "private, " \
            + "stewards_fph_list, " \
            + "default_currency_fph, " \
            + "owner_fph " \
            + "FROM namespaces WHERE entity_fph = ?", (namespace_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return False, "", "Namespace not registered"
    active = bool(result[0])
    private = bool(result[1])
    stewards_list = pickle.loads(result[2])
    default_currency_fph = result[3]
    owner_fph = result[5]
    return active, private, stewards_list, default_currency_fph, owner_fph, ""

#==============================================================================
## Check whether an entity is currently active:

def entity_is_active(entity_id, entity_type):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if not (entity_type in etypes):
        return False, entity_id + " is not " + entity_type
    if entity_type == "currency": # inconveniently irregular plural
        table_name = "currencies"
    else:
        table_name = entity_type + "s"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT active FROM " + table_name + " WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return False, "Entity " + entity_fph + " not found"
    return bool(result[0]), ""

#==============================================================================
## Check whether a *namespace* or *currency* is private:

def privacy(entity_id, entity_type):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if not (entity_type in etypes):
        return False, "No " + entity_type + " is registered for " + entity_id
    if not (entity_type in ["namespace", "currency"]):
        return False, "Entities of type " + entity_type + " have no privacy"
    if entity_type == "currency": # inconveniently irregular plural
        table_name = "currencies"
    else:
        table_name = entity_type + "s"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT private FROM " + table_name + " WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return False, "Entity " + entity_fph + " not found"
    return bool(result[0]), ""

#==============================================================================
## Get owner of entity:

def get_owner(entity_id, entity_type):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if not (entity_type in etypes):
        return False, "No " + entity_type + " is registered for " + entity_id
    if not (entity_type in ["account", "namespace", "ahid", "secid"]):
        return "", entity_id + " is not an owned type"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT owner_fph FROM " + entity_type + "s WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return "", "No entity " + entity_hrns + " of type " + entity_type
    return result[0]

#==============================================================================
## Listr all *accounts* in the specified *currency*:

def list_currency_accounts(currency_id):
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not ("currency" in etypes):
        return []
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_fph FROM currency_accounts WHERE currency_fph = ?",
            (currency_fph,)
        )
        results = cursor.fetchall()
        cursor.close()
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

def retrieve_primid_access_details(primid_id):
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if m:
        return "", "", "", m
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, pin, access_token_hash " \
            + "FROM primids WHERE entity_fph = ?", (primid_fph,)
        )
        result = cursor.fetchone()
        if result is not None:
            password_hash = result[0]
            pin = result[1]
            access_token_hash = result[2]
            return password_hash, pin, access_token_hash, ""
        else:
            "", "", "", primid_id + " authentication data unavailable"

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
        username, parent_id,
        realname, # optional
        email_address_1, email_address_2, # the latter is optional
        password, pin, # 6 digits
        currency_id # for the initial *ahid*|*currency* pairing
    ):
    errors = ""
    if not re_pin.match(pin):
        errors += "Invalid PIN provided\n"
        return "", "", "", errors
#    print("parent_id = " + parent_id)
    parent_fph, parent_hrns, etypes, m = identify_entity(parent_id)
    if not parent_fph:
        errors += "Invalid parent\n"
        errors += m
        return "", "", "", m # parent is invalid
    if realname:
        if not re_realname.match(realname):
            errors += "Invalid real name \"" + realname + "\" discarded " \
                   + "so the primid has been created without a real name.\n"
            primid_realname = ""
    if not email_address_1:
        # The *primid* cannot be created if no valid primary email address has
        # been provided:
        delete_fph_from_map(primid_fph)
        errors += "No primary email address provided\n"
        return "", "", "", errors
    if not re_email.match(email_address_1):
        delete_fph_from_map(primid_fph)
        errors += "Invalid entry: primary email address\n"
        return "", "", "", errors
    if email_address_2:
        # If an invalid secondary email address is provided it is discarded and
        # the *primid* is created with only a primary email address:
        if not re_email.match(email_address_2):
            errors += "Invalid secondary email address " + email_address_2 \
                   + " has been discarded.\n"
            email_address_2 = ""
    # The access authentication details are now added:
    access_token = generate_access_token()
    access_token_hash = auth_hash(access_token)

    # NB, when a new *primid* is created the following additional entities (of
    # which it will be the owner or a steward) are created and registered to
    # the same identifer:
    # - a *namespace* (the root of this *primid*s private *namesapce* tree)
    # - a *currency* (of which this *primid* will be the initial steward)
    # - an *ahid* (since any *primid* must serve also as an *ahid*)
    # - an *account* owned by this *primid*
    # However, a *secid* cannot be created using this identifier.

    if not re_slatename.match(username):
#        print("Invalid name provided: " + username)
        errors += "Invalid name provided\n"
        return "", "", "", errors
    primid_hrns = username + NSS + parent_hrns
    if identifier_unregistered(primid_hrns):
        primid_fph = register_identifier(primid_hrns)
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_hrns)
    print("new_primid: " + primid_fph + " > " + primid_hrns)
    if ("primid" in etypes):
        # The identifier of any existing *primid* cannot be used for another.
        errors += primid_hrns + " exists already (primid)\n"
        return "", "", "", errors
    # We can now register a *primid* for this identifier:
#    print("We can now register a *primid* for " + primid_hrns)
    register_entity_type(primid_fph, "primid")


    # At the point of its creation, a *primid* has no *secids", so an empty
    # list is created:
    secids_fph_list = []


    # This *primid* will be the owner of a an *account* sharing the same
    # identifier, but it cannot be created at this point because the *primid*
    # has not yet been added to the primids table. The empty accounts list is
    # created here in preparation for that action in due course:
    accounts_fph_list = []



    # A second *account* is created for use in the associated *ahid*|*currency*
    # pairing:
#    account_fph, account_hrns, \
#    m = new_pairing(primid_fph, primid_hrns, currency_id)
#    accounts_fph_list.append(account_fph)


    ahid_hrns = currency_hrns = primid_hrns # lest we forget

#    pmap = {ahid_hrns_hrns : {}}
#    print("new_primid( ): pmap = ", end="")
#    print(pmap)

    # This *primid* is the initial steward of a *namespace* and a *currency*
    # having the same FPH:
#    nstewardships_fph_list = [primid_fph]
#    cstewardships_fph_list = [primid_fph]
    nstewardships_fph_list = []
    cstewardships_fph_list = []
    # POTENTIAL TRAP: This means that whenever either a *namespace* or a
    # *currency* is created, an entity of the other type must be created and
    # registered for the same identifier.
    default_currency_fph = primid_fph
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO primids (" \
            + "entity_fph, " \
            + "primid_realname, " \
            + "primid_email_1_hash, " \
            + "primid_email_2_hash, " \
            + "secids_fph_list, " \
            + "pmap, " \
            + "nstewardships_fph_list, " \
            + "cstewardships_fph_list, " \
            + "password_hash, " \
            + "pin, " \
            + "access_token_hash" \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                primid_fph,
                realname,
                auth_hash(email_address_1),
                auth_hash(email_address_2),
                pickle.dumps(secids_fph_list),
                pickle.dumps({}),
                pickle.dumps(nstewardships_fph_list),
                pickle.dumps(cstewardships_fph_list),
                #password_already_hashed,    # restored 2024-11-10 19.50
                auth_hash(password),        # restored 2024-11-10 19.50
                pin,
                auth_hash(access_token),
            )
        )
        conn.commit()
        cursor.close()

    # The new *primid* having been added to the primids table, the other
    # entities sharing its identifier can now be created.

    # A new *currency* and *namespace* are created with the same identifier as
    # the *primid* which also serves as the initial steward of both.
    currency_fph, currency_hrns, \
    m = new_currency(
            username, parent_fph,   # identifier
            primid_fph,             # initial steward
            "", "",                 # prefix | suffix
            username                # default account name
        )
#    if m:
#        print("m1: " + m)

#    print("new_primid: (A) currency_hrns = " + currency_hrns)

    # The new *ahid*|*currency* pairing-indexed *account* is created with this
    # *primid* as its owner, where the *ahid* shares the same identifier as the
    # *primid*:
    account_fph, account_hrns, \
    m = new_pairing(
            primid_fph,     # *ahid* belongs to *primid* and shares identifier;
            primid_hrns,    # *account* HRNS combines *ahid* & *currency*; and
            currency_fph    # *currency* was created immediately before this.
        )
#    if m:
#        print("m2: " + m)

#    print("new_primid: (B) account_hrns = " + account_hrns)

    # A second new *account* is created  with the same identifier as the
    # *primid* which also serves as its initial steward:
    account_fph, account_hrns, \
    m = new_account(
            username, parent_fph,   # identifier
            primid_fph,             # owner (*ahid* or *secid*) identifier
            currency_fph            # *currency* identifier
        )
#    if m:
#        print("m3: " + m)

#    print("new_primid: (C) account_hrns = " + account_hrns)




    return primid_fph, primid_hrns, access_token, errors

# Although the initial access token is generated automatically here, it may be
# updated by the *primid* at any time.

#==============================================================================
## A new *secid* is created:

def new_secid(
        username,
        parent_id,
        primid_fph
    ):
    errors = ""
    parent_fph, parent_hrns, etypes, m = identify_entity(parent_id)
    if not parent_fph:
        return "", "", "", "Invalid parent FPH: " + parent_id
    if not re_slatename.match(username):
        return "", "", "", "Invalid name provided"
    secid_hrns = username + NSS + parent_hrns
    secid_fph, secid_hrns, etypes, m = identify_entity(secid_hrns)
    if not secid_fph:
        # If the identifier is not registered, that can be done now (creating
        # the HRNS>FPH and FPH>HRNS mappings):

#        print("identifier_hrns 4 = " + secid_hrns)

        secid_fph = register_identifier(secid_hrns)
        if not secid_fph: # Unable to register identifier
            return "", "", "", "Unable to register " + secid_hrns
    elif ("secid" in etypes):
        # The identifier of an existing *secid* cannot be used for another.
        return "", "", "", secid_hrns + " exists already (secid)"
    else:
        # We can now register a *secid* for this identifier:
        register_entity_type(secid_fph, "secid")
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
#        # TEST STUFF
#        with open("secid_creation_dump.txt", "a") as f:
#            f.write(
#                "secid " + secid_hrns + " (" + secid_fph + ") " \
#                + "added for primid " + fph_to_hrns(primid_fph) \
#                + " (" + primid_fph + ")\n"
#            )
#        # END OF TEST STUFF
    return secid_fph, secid_hrns, ""

#==============================================================================
## A new *ahid* is created:

### THIS may not be needed, given that in  new_pairing( )  a new *ahid*
###      entity is created directly.

def new_ahid(
        ahidname,
        parent_id,
#        initial_account_fph, # the first *account* assigned to this *ahid*
        primid_fph
    ):
    if not re_slatename.match(ahidname):
#        print("new ahid: invalid name provided")
        return "", "", "Invalid name provided"
    parent_fph, parent_hrns, etypes, m = identify_entity(parent_id)
    if not parent_fph:
#        print("new ahid: invalid parent " + parent_id)
        return "", "", m # parent is invalid
    if not ("namespace" in etypes):
#        print("new ahid: parent " + parent_id + " is not registered")
        return "", "", "Parent namespace not registered"
    ahid_hrns = ahidname + NSS + parent_hrns
    # Does this *ahid*'s identifier exist already?
    if identifier_unregistered(ahid_hrns):
#        print("new ahid: identifier " + ahid_hrns + " not yet registered")
        ahid_fph = register_identifier(ahid_hrns)
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_hrns)
    if not ("ahid" in etypes):
        register_entity_type(ahid_fph, "ahid")
        with sqlite3.connect(ENTITIES_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ahids (" \
                + "entity_fph, " \
                + "primid_fph, " \
                + "accounts_fph_list, " \
                + "active" \
                + ") VALUES (?, ?, ?, ?)",
                (ahid_fph, primid_fph, pickle.dumps([]), 1)
            )
            conn.commit()
            cursor.close()
    if not ("namespace" in etypes):
        # If a new *namespace* is created here
        # (1) the *ahid*'s owner is assigned the initial stewardship, and
        # (2) it is assigned the default *currency* of its parent *namespace*.
        stewards_fph_list = []
        stewards_fph_list.append(primid_fph)
        active, sandbox, private, owner_fph, currency_fph, stewards_list, \
        m = get_namespace_properties(parent_fph)
        with sqlite3.connect(ENTITIES_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO namespaces (" \
                + "entity_fph, " \
                + "stewards_fph_list, " \
                + "default_currency_fph" \
                + ") VALUES (?, ?, ?)",
                (
                    ahid_fph, # same identifier
                    pickle.dumps(stewards_fph_list),
                    currency_fph
                )
            )
            conn.commit()
            cursor.close()
    return ahid_fph, ahid_hrns, ""

#==============================================================================
## A new *namespace* is created:

def new_namespace(
        nsname,
        parent_id,
        currency_id,
        steward_id
    ):
    if not re_slatename.match(nsname):
        return "", "", nsname + " is not a valid name"
    # The substrate is a special case of parent *namespace* (nameless).
    # No entity other than a *namespace* can be created with the substrate
    # as its parent.
    if parent_id == SUBSTRATE_FPH:
        parent_hrns = ""
        parent_fph = parent_id
        etype = "namespace"
        namespace_hrns = nsname
    else:
        parent_fph, parent_hrns, etypes, m = identify_entity(parent_id)
        if not parent_fph: # parent *namespace* identifier is not registered
            return "", "", "Parent namespace does not exist"
        namespace_hrns = nsname + NSS + parent_hrns # tentative HRNS
    if identifier_unregistered(namespace_hrns):
        namespace_fph = register_identifier(namespace_hrns)
    namespace_fph, namespace_hrns, etypes, m = identify_entity(namespace_hrns)
    if ("namespace" in etypes):
        # The identifier of an existing *namespace* cannot be used for another.
        return "", "", namespace_hrns + " exists already (namespace)"
    else:
        register_entity_type(namespace_fph, "namespace")
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not currency_fph:
        return "", "", currency_id + " is not a registered identifier (14)"
    if not ("currency" in etypes):
        return "", "", currency_hrns + " has no registered currency"
    steward_fph, steward_hrns, etypes, m = identify_entity(steward_id)
    if not steward_fph:
        return "", "", steward_id + " is not a registered identifier (15)"
    if not ("primid" in etypes):
        return "", "", steward_hrns + " has no registered primid"
    # We can now register a *namespace* for this identifier:
    register_entity_type(namespace_fph, "namespace")
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO namespaces (" \
            + "entity_fph, " \
            + "stewards_fph_list, " \
            + "default_currency_fph" \
            + ") VALUES (?, ?, ?)",
            (
                namespace_fph,
                pickle.dumps([steward_fph]),
                currency_fph
            )
        )
        conn.commit()
        cursor.close()
    return namespace_fph, namespace_hrns, ""

#==============================================================================
## A new currency is added:

def new_currency(
        currency_name,
        parent_fph,
        initial_steward_fph,
        currency_prefix,
        currency_suffix,
        default_account_name
    ):
    # The initial *account* in this *currency* is assigned to its initial
    # steward (which must exist already).
    parent_fph, parent_hrns, etypes, m = identify_entity(parent_fph)
    if not parent_fph:
        return "", "", "Parent namespace does not exist"
    if not re_slatename.match(currency_name):
        return "", "", currency_name + " is not a valid name"
    # If no other name is specified, new *accounts* in this *currency* are
    # assigned this default name.
    if default_account_name:
        if not re_slatename.match(default_account_name):
            return "", "", default_account_name + " is not a valid name"
    currency_hrns = currency_name + NSS + parent_hrns # tentative HRNS
    if identifier_unregistered(currency_hrns):
        currency_fph = register_identifier(currency_hrns)
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_hrns)
    if ("currency" in etypes):
        return "", "", "Currency " + currency_hrns + " is already registered"
    register_entity_type(currency_fph, "currency")
    # Now add *currency* specific properties:
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
            cstewardships_fph_list = pickle.loads(cstewardships_fph_blob)
        else:
            cstewardships_fph_list = []
        if not (currency_fph in cstewardships_fph_list):
            cstewardships_fph_list.append(currency_fph)
            cstewardships_fph_blob = pickle.dumps(cstewardships_fph_list)
            cursor.execute(
                "UPDATE primids SET cstewardships_fph_list = ? " \
                + "WHERE entity_fph = ?",
                (cstewardships_fph_blob, initial_steward_fph)
            )
            conn.commit()
        cursor.close()

    # A new *namespace* is created with the same identifier as the new
    # *currency* (which is assigned as its default *currency*) and having the
    # same initial steward.
    namespace_fph, namespace_hrns, \
    m = new_namespace(
            currency_name, parent_fph,  # identifier
            currency_fph,               # default *currency* for
            initial_steward_fph         # initial steward
        )

    return currency_fph, currency_hrns, ""

#==============================================================================
## A new account is created in a specified currency:

def new_account(
        account_name, parent_id,    # identifier
        owner_id,                   # *ahid* or *secid*
        currency_id
    ):
    errors = ""
    parent_fph, parent_hrns, etypes, m = identify_entity(parent_id)
    if not parent_fph:
#        print("new_account: invalid parent FPH: " + parent_id)
        return "", "", "Invalid parent FPH: " + parent_id
    # The *account* name may take either of two forms:
    # (1) that of a typical identifier (if  the *account* is for a "secid"), or
    # (2) a form encoded automatically from the identifiers of an *ahid* and
    #     a *currency* (if  the *account* is for an "ahid"|*currency*)pairing).
    account_for_secid = False
    account_for_pairing = False
#    print("new_account: " + account_name)
    if re_slatename.match(account_name):
        account_for_secid = True
    elif re_pan1.match(account_name):
        pan = account_name.split("_&_")
        pan_ahid = pan[0].replace("_", "")
        pan_currency = pan[0].replace("_", "")
#        print("new_account: " + pan_ahid + " & " + pan_currency)
        if (re_pan2.match(pan_ahid) and re_pan2.match(pan_currency)):
            account_for_pairing = True
    if not (account_for_secid or account_for_pairing):
        return "", "", "Invalid account name provided"
    account_hrns = account_name + NSS + parent_hrns
#    print("new_account: account_hrns = " + account_hrns)
    if identifier_unregistered(account_hrns):
#        print("new_account: registering identifier " + account_hrns)
        account_fph = register_identifier(account_hrns)
    account_fph, account_hrns, etypes, m = identify_entity(account_hrns)
    if ("account" in etypes):
        # The identifier of an existing *account* cannot be used for another.
        return "", "", account_hrns + " exists already (account)"
    register_entity_type(account_fph, "account")

    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not currency_fph:
        return "", "", currency_id + " is not a registered identifier"
    if not ("currency" in etypes):
        return "", "", currency_fph + " has no registered currency"
    currency_fph, currency_hrns, active, private, sandbox, \
    type, category, units, metrical_equivalence, dimensions, \
    prefix, suffix, default_account_name, \
    stewards_list, m = get_currency_properties(currency_fph)
    if not re_slatename.match(account_name): # invalid *account* name provided
#        flash(
#            "Invalid account name provided, so currency's default (" \
#            + default_account_name + ") has been used."
#        )
        account_name = default_account_name # from *currency*
    account_fph = register_identifier(account_hrns)
    register_entity_type(account_fph, "account")
    # The owner may be either an *ahid* or a *secid".
    owner_fph, owner_hrns, etypes, m = identify_entity(owner_id)
    if not owner_fph:
        return "", "", "Invalid owner FPH: " + owner_fph
    if ("ahid" in etypes):
        table = "ahids"
    elif ("secid" in etypes):
        table = "secids"
    else:
        return "", "", owner_fph + " is not a valid agent type"
    # Now add *account* specific properties:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accounts (" \
            + "entity_fph, account_owner_fph, account_currency_fph, " \
            + "balance, volume, account_type"
            + ") VALUES (?, ?, ?, ?, ?, ?)",
            (account_fph, owner_fph, currency_fph, 0, 0, "money")
        )
        conn.commit()
        cursor.execute(
            "SELECT accounts_fph_list FROM " + table + " WHERE entity_fph = ?",
            (owner_fph,)
        )
        result = cursor.fetchone()
        accounts_fph_blob = result[0]
        accounts_fph_list = pickle.loads(accounts_fph_blob)
        accounts_fph_list.append(account_fph)
        accounts_fph_blob = pickle.dumps(accounts_fph_list)
        cursor.execute(
            "UPDATE " + table + " SET accounts_fph_list = ?" \
            + " WHERE entity_fph = ?", (accounts_fph_blob, owner_fph)
        )
        cursor.execute(
            "INSERT INTO currency_accounts (currency_fph, account_fph) " \
            + "VALUES (?, ?)", (currency_fph, account_fph)
        )
        conn.commit()
        cursor.close()
    if m:
        return "", "", m
    else:
        return account_fph, account_hrns, ""

#==============================================================================
##

def get_namespace_properties(namespace_id):
    namespace_fph, namespace_hrns, etypes, m = identify_entity(namespace_id)
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
## Set the default *currency* for the *namespace*. This will usually be set
## only when the *namespace* is created but can be changed subsequently if
## required.

def set_default_currency(namespace_id, currency_id):
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not currency_fph:
        return "Currency cannot be identified"
    entity_fph, entity_hrns, etypes, m = identify_entity(namespace_id)
    if not entity_fph:
        return "Entity " + entity_id + " cannot be identified"
    if not ("namespace" in etypes):
        return entity_hrns + " has no namespace type"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE entities_registered SET default_currency_fph = ? " \
            + "WHERE entity_fph = ?", (currency_fph, entity_fph)
        )
        conn.commit()
        cursor.close()
    return ""

#------------------------------------------------------------------------------
##

def get_default_currency(namespace_id):
    entity_fph, entity_hrns, etypes, m = identify_entity(namespace_id)
    if not entity_fph:
        return "Entity " + entity_id + " cannot be identified"
    if not ("namespace" in etypes):
        return namespace_hrns + " is not a namespace type"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT default_currency_fph FROM namespaces " \
            + "WHERE entity_fph = ?", (entity_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        return "Default currency cannot be identified"
    else:
        return result[0]

#==============================================================================
##

def get_currency_properties(currency_id):
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if m:
        return "", "", False, False, False, "", "", "", [], m
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT active, private, sandbox, " \
            + "type, category, units, metrical_equivalence, dimensions, " \
            + "currency_prefix, currency_suffix, default_account_name, " \
            + "stewards_fph_list FROM currencies WHERE entity_fph = ?",
            (currency_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        m = "Currency " + fph_to_hrns(currency_fph) + " not found"
        return "", "", False, False, False, "", "", "", [], m
    #
    active = bool(result[0])
    private = bool(result[1])
    sandbox = bool(result[2])
    type = result[3]
    category = result[4]
    units = result[5]
    metrical_equivalence = result[6]
    dimensions = result[7]
    prefix = result[8]
    suffix = result[9]
    default_account_name = result[10]
    stewards_fph_blob = result[11]
    stewards_list = pickle.loads(stewards_fph_blob)
    return currency_fph, currency_hrns, active, private, sandbox, \
           type, category, units, metrical_equivalence, dimensions, \
           prefix, suffix, default_account_name, stewards_list, ""

#==============================================================================
##

def get_currency_name(currency_fph):
    hrns = fph_to_hrns(currency_fph)
    if hrns == "":
        return ""
    else:
        hrnsa = hrns.split(NSS)
        return hrnsa[0]

#==============================================================================
## List the *identity*'s *accounts*:
#
# This will list all *accounts* belonging to a *primid*, *ahid* or "secid", the
# *account* itself identifying its *currency*.

def list_accounts(identity_id, identity_etype):
    identity_fph, identity_hrns, etypes, m = identify_entity(identity_id)
    if not identity_fph:
        return [], identity_id + " is not a registered identifier (3)"
    if not (identity_etype in etypes): # *primid*, *ahid* or *secid*
        return [], identity_hrns + " has no registered " + identity_etype
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT accounts_fph_list FROM " + identity_etype + "s " \
            + "WHERE entity_fph = ?", (identity_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            accounts_fph_list = []
            accounts_fph_blob = pickle.dumps(accounts_fph_list)
            cursor.execute(
                "UPDATE " + identity_etype + "s SET accounts_fph_list = ? " \
                + "WHERE entity_fph = ?", (accounts_fph_blob, identity_fph)
            )
            conn.commit()
            cursor.close()
            return [], identity_hrns + " has no accounts."
        else:
            cursor.close()
            accounts_fph_blob = result[0]
            accounts_fph_list = pickle.loads(accounts_fph_blob)
    return accounts_fph_list, ""

#==============================================================================
## List the *identity*'s *accounts* in a specified *currency*:
#
# This will list all *accounts* in a specified *currency* belonging to a
# *primid*, *ahid* or "secid".

def list_id_accounts_in_currency(identity_id, identity_etype, currency_id):
    currency_fph, currency_hrns, etypes, m = identify_entity(identity_id)
    if not currency_fph:
        return [], currency_id + " is not a registered identifier (4)"
    if not ("currency" in etypes):
        return [], "No currency is registered for " + currency_hrns
    accounts_fph_list, m = list_accounts(identity_id, identity_etype)
    if m:
        return [], m
    accounts_in_currency = []
    for account_fph in accounts_fph_list:
        account_currency_fph, m = get_account_currency(account_fph)
        if m:
            return [], m
        if account_currency_fph == currency_fph:
            accounts_in_currency.append(account_fph)
    return accounts_in_currency, ""

#==============================================================================
## List the *secid*'s accounts: #

def list_secid_accounts(secid_fph):
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT accounts_fph_list FROM secids WHERE entity_fph = ?",
            (secid_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            accounts_fph_list = []
            accounts_fph_blob = pickle.dumps(accounts_fph_list)
            cursor.execute(
                "UPDATE secids SET accounts_fph_list = ? WHERE entity_fph = ?",
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

def list_agent_accounts(agent_fph, etype):

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

def get_account_currency(account_id):
    account_fph, account_hrns, etypes, m = identify_entity(account_id)
    if not account_fph:
        return "", account_id + " is not a registered identifier (5)"
    if not ("account" in etypes):
        return [], "No account is registered for " + account_hrns
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_currency_fph FROM accounts WHERE entity_fph = ?",
            (account_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is not None:
        currency_fph = result[0]
    else:
        currency_fph = ""
    return currency_fph, ""

#==============================================================================
# List all *accounts* in the specified *currency*:
#
# A *currency* will usually have a large number of *accounts*, so these are
# stored in a separate table rather than in a pickled blob in the *currencies*
# table.

def list_all_accounts_in_currency(currency_id):
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not currency_fph:
        return [], currency_id + " is not a registered identifier (6)"
    if not ("currency" in etypes):
        return [], "No currency registered for " + currency_hrns
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT entity_fph FROM accounts WHERE account_currency_fph = ?",
            (currency_fph,)
        )
        result_list = cursor.fetchall()
        cursor.close()
    if result_list is None:
        return [], "Currency " + currency_hrns + " has no accounts."

    accounts_fph_list = []
    for result in result_list:
        account_fph = result[0]
        accounts_fph_list.append(account_fph)
    return accounts_fph_list, ""

#==============================================================================
# Identify the *account* (if any) in which the specified *identity* has access
# to the specified *currency*: KEEP
#
# NB, where a *primid*, an *ahid* and a *secid* share the same identifier they
# also share the same set of *accounts*, so a *secid* will not generally be
# registered to an identifier if it has a *primid* or an *ahid*, and if it is
# it will be ignored.
# i.e. valid combinations for a specific identifier are:
#   | *primid* | *ahid*   |          |      *currency*|*ahid* -> *account*
#   |          | *ahid*   |          |      *currency*|*ahid* -> *account*
#   |          |          | *secid*  |      *secid* -> *account*
#
# The following combinations are also possible for a specific identifier:
#   | *primid* |          |          |      no *account*
#   | *primid* | *ahid*   | *secid*  |      *currency*|*ahid* -> *account*
#   | *primid* |          | *secid*  |      *secid* -> *account*
#   |          | *ahid*   | *secid*  |      *currency*|*ahid* -> *account*
# The system will still function in these combinations, but they should never
# occur by design.
#
# Therefore,
# - *accounts* are no longer held by a *primid*
# - each *account* belongs to an *ahid* or a *secid*
# - each *account* is addressed either directly (by its own identifier) or
#   indirectly (by a pairing of *currency* and *ahid* identifiers)
# - each *account* identifies the *ahid* or *secid* to which it belongs
# - each *account* identifies its *currency*
# - each *currency* lists every *account* belonging to it
# - each *ahid* or *secid* identifies the *primid* to which it belongs
# - each *primid* lists every *ahid* and *secid* belonging to it
# - each *primid* lists every *currency* and *namespace* in its stewardship
# - each *primid* holds a *currency*|*ahid* pairing matrix indexing *account*

def list_id_accounts_in_currency(identity_id, identity_etype, currency_id):
    if not (identity_etype in ["ahid", "secid"]):
        return "", identity_etype + " is not an identity type"
    identity_fph, identity_hrns, etypes, m = identify_entity(identity_id)
    if not identity_fph:
        return "", identity_id + " is not a registered identifier (7)"
    if not (identity_etype in etypes):
        return "", "No " + identity_etype + " registered for " + identity_hrns
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not currency_fph:
        return "", currency_id + " is not a registered identifier (8)"
    if not ("currency" in etypes):
        return "", "No currency is registered for " + currency_hrns
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT entity_fph FROM accounts " \
            + "WHERE account_currency_fph = ?, account_owner_fph = ?",
            (currency_fph, primid_fph)
        )
        result_list = cursor.fetchall()
        cursor.close()
    if result_list is None:
        return [], "No results found."
    accounts_fph_list = []
    for account_fph in result_list:
        accounts_fph_list.append(account_fph)
    return accounts_fph_list, ""

#==============================================================================
## List the *primid*'s *account*s' *currencies*:
#
# For a specified *primid*, return a list the *currencies* in which it has an
# *account*

def list_primid_currencies(primid_fph): # in which an primid has accounts
    accounts_fph_list, m = list_primid_accounts(primid_fph)
    currencies_fph_list = []
    for account_fph in accounts_fph_list:
        currencies_fph_list.append(get_account_currency(account_fph))
    return currencies_fph_list

#==============================================================================
## List the *secid*'s *account*s' *currencies*:
#
# For specified *secid*, return a list the *currencies* in which it has an
# *account*

def list_secid_currencies(secid_fph):
    accounts_fph_list, m = list_secid_accounts(secid_fph)
    currencies_fph_list = []
    for account_fph in accounts_fph_list:
        currencies_fph_list.append(get_account_currency(account_fph))
    return currencies_fph_list

#==============================================================================
#

def list_secids(primid_id):
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if not primid_fph:
        return [], primid_id + " is not a registered identifier (9)"
    if not ("primid" in etypes):
        return [], "No primid registered for " + primid_hrns
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Retrieve the list of *secids* for this *primid*:
        cursor.execute(
            "SELECT secids_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        secids_fph_list = []
    else:
        secids_fph_list = pickle.loads(result[0])
    return secids_fph_list


#==============================================================================
#

def list_ahids(primid_id):
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if not primid_fph:
        return [], primid_id + " is not a registered identifier (10)"
    if not ("primid" in etypes):
        return [], "No primid registered for " + primid_hrns
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Retrieve the list of *secids* for this *primid*:
        cursor.execute(
            "SELECT ahids_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        ahids_fph_list = []
    else:
        ahids_fph_list = pickle.loads(result[0])
    return ahids_fph_list

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

def list_active_namespaces():
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT entity_fph FROM namespaces WHERE active = 1")
        result_list = cursor.fetchall()
        cursor.close()
    if result_list is None:
        return []
    active_namespaces = []
    for namespace in result_list:
        active_namespaces.append(result[0])
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
        cursor.execute("SELECT entity_fph FROM namespaces", (namespace_fph,))
        results = cursor.fetchall()
        cursor.close()
    if results is None:
        return []
    namespaces = []
    for result in results:
        namespaces.append(result[0])
    return namespaces

# List all currencies:

def list_all_currencies():
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT entity_fph FROM currencies", (namespace_fph,))
        results = cursor.fetchall()
        cursor.close()
    if results is None:
        return []
    currencies = []
    for result in results:
        currencies.append(result[0])
    return currencies

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

    entity_current_hrns = fph_to_hrns(entity_fph).split(NSS)
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

def get_account_properties(account_id):
    account_fph, account_hrns, etypes, m = identify_entity(account_id)
    if not account_fph:
        return "", "", 0, 0, False, "No entity at " + account_id
    if not ("account" in etypes):
        return "", "", 0, 0, False, "No account at " + account_hrns
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT " \
            + "account_owner_fph, " \
            + "account_currency_fph, " \
            + "balance, " \
            + "volume, " \
            + "active " \
            + "account_type, " \
            + "category, " \
            + "units, " \
            + "metrical_equivalence, " \
            + "dimensions, " \
            + "vector, " \
            + "vector_map, " \
            + "matrix, " \
            + "matrix_map, " \
            + "ts_pointer " \
            + "FROM accounts WHERE entity_fph = ?",
            (account_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return "", "", 0, 0, False, "Account not found"
    # The owner of this *account* may be either an *ahid* or a *secid*.
    owner_fph, owner_hrns, etypes, m = identify_entity(result[0])
    if not (("ahid" in etypes) or ("secid" in etypes)):
        return "", "", 0, 0, False, "Account  has no owner"
#    ahid_fph, ahid_hrns, etypes, m = identify_entity(result[1])
#    if not ("ahid" in etypes):
#        return "", "", "", 0, 0, False, "Account  has no owner"
    currency_fph = result[1]
    balance = result[2]
    volume = result[3]
    active = bool(result[4])
#    return currency_fph, owner_fph, ahid_fph, balance, volume, active, ""
    return currency_fph, owner_fph, balance, volume, active, ""



#
#==============================================================================
## Retrive the status of an account:
#
# returns:  exists          (boolean),
#           active          (boolean),
#           currency        (FPH),
#           owner           (FPH),
#           errors          text

def account_status(account_fph):
    currency_fph, owner_fph, balance, volume, active, \
    m = get_account_properties(account_fph)
    if m:
#        print("account_status( ) error: " + m)
        return False, False, "", "", 0, 0, m
    #return True, active, currency_fph, owner_fph, balance, volume, ""
    return active, currency_fph, owner_fph, balance, volume, ""



#==============================================================================
##

def get_primid_properties(primid_id):
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if not primid_fph:
#        print("No identifier registered for " + primid_id)
        return False, False, [], [], {}, [], [], \
               "No identifier registered for " + primid_id
    if not ("account" in etypes):
#        print("No account registered for " + primid_hrns)
        return False, False, [], [], {}, [], [], \
               "No account registered for " + primid_id
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT " \
            + "active, " \
            + "administrator, " \
            + "ahids_fph_list, " \
            + "secids_fph_list, " \
            + "pmap, " \
            + "nstewardships_fph_list, " \
            + "cstewardships_fph_list " \
            + "FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return False, False, [], [], {}, [], [], \
               "Primid " + primid_hrns + " not found"
    active = bool(result[0])
    administrator = bool(result[1])
    ahids_fph_list = pickle.loads(result[2])
    secids_fph_list = pickle.loads(result[3])
    pmap = pickle.loads(result[4])
    nstewardships_fph_list = pickle.loads(result[5])
    cstewardships_fph_list = pickle.loads(result[6])
    return active, administrator, \
           ahids_fph_list, secids_fph_list, pmap, \
           nstewardships_fph_list, cstewardships_fph_list, ""


#==============================================================================
##

def get_ahid_properties(ahid_id):
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_id)
    if not ahid_fph:
        return False, "", [], "No entity registered for " + ahid_id
    if not ("account" in etypes):
        return False, "", [], "No account registered for " + ahid_hrns
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT " \
            + "active, " \
            + "primid_fph, " \
            + "accounts_fph_list "
            + "FROM ahids WHERE entity_fph = ?",
            (ahid_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return False, "", [], "Secid not found"
    active = bool(result[0])
    primid_fph = result[1]
    accounts_fph_list = pickle.loads(result[2])
    return active, primid_fph, accounts_fph_list, ""


#==============================================================================
##

def get_secid_properties(secid_id):
    secid_fph, secid_hrns, etypes, m = identify_entity(secid_id)
    if not secid_fph:
        return False, "", [], "No entity registered for " + secid_id
    if not ("account" in etypes):
        return False, "", [], "No account registered for " + secid_hrns
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT " \
            + "active, " \
            + "primid_fph, " \
            + "accounts_fph_list " \
            + "FROM secids WHERE entity_fph = ?",
            (secid_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return False, "", [], "Secid not found"
    active = bool(result[0])
    primid_fph = result[1]
    accounts_fph_list = pickle.loads(result[2])
    return active, primid_fph, accounts_fph_list, ""


#==============================================================================
## Add a stewardship to a *primid* and a steward to a *namespace* or *currency*:

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
    if ("namespace" in etypes):
        table = "namespaces"
    elif ("currency" in etypes):
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

def list_active_namespaces(ancestor_namespace_id = ""): # FPH or HRNS

    errors = ""

    if ancestor_namespace_id == "": # universal substrate namespace
        ancestor_fph = SUBSTRATE_FPH
        ancestor_hrns = ""
        etype = "namespace"
        m = ""
    else:
        ancestor_fph, \
        ancestor_hrns, \
        etypes, \
        m = identify_entity(ancestor_namespace_id)
        if m or (etype != "namespace"):
            return [SUBSTRATE_FPH], m
        if m:
            errors += m

    # First the *namespace* trees are selected where the node root *namespace*
    # is active and has the specified ancestor *namespace* as its parent:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT entity_fph FROM entities_registered " \
            + "WHERE entity_type = ? AND active = ?",
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
            branch = namespace_hrns.replace(NSS + ancestor_hrns, "")
            if branch:
                namespace_fph_list.append(namespace_fph)

    return namespace_fph_list, ""


#==============================================================================
# Get the *primid* to which a *secid* belongs:

def get_primid(id_id): # *secid* or *ahid*
    # (1) Each *ahid* or *secid* belongs to one *primid*
    # (2) Each *primid* may have any number of *ahid* or *secids*
    # (3) The identifier of a *primid* also identifies the first *ahid* in the
    #     set available to that *primid*. In effect, this particular *ahid*
    #     belongs to that *primid*.
    id_fph, id_hrns, etypes, m = identify_entity(id_id)
    if not id_fph:
        return "", d_id + " is not a registered identifier"
    if ("ahid" in etypes):
        table = "ahids"
    elif ("secid" in etypes):
        table = "secids"
    else:
        return "", id_hrns + " identifies neither an ahid nor a secid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT primid_fph FROM " + table + " WHERE entity_fph = ?",
            (id_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return "", "Owner not recorded (this should never happen)"
    owner_fph = result[0]
    return owner_fph, ""

#==============================================================================

def get_ahid_primid(ahid_id):
    # (1) Each *ahid* belongs to one *primid*
    # (2) Each *primid* may have any number of *ahid*
    # (3) A *primid* may belong to itself as an *ahid*
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_id)
    if not ahid_fph:
#        print(ahid_id + " is not a registered identifier (11)")
        return ""
    if not ("ahid" in etypes):
#        print(ahid_hrns + " has no ahid")
        return ""
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT primid_fph FROM ahids WHERE entity_fph = ?",
            (ahid_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return ""
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
            "SELECT primid_email_1_hash, primid_email_2_hash FROM primids " \
            + "WHERE entity_fph = ?",
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
    n = hrns.split(NSS)
    name = n.pop([0])
    namespace_hrns = NSS.join(n)
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
    names = identifier_hrns.split(NSS)
    name = names.pop(0)
#    print("split: " + name + " & ", end="")
#    print(names)
    parent_hrns = NSS.join(names).strip(NSS)
#    print(">>> " + name + ":" + parent_hrns)
    return name, parent_hrns


#==============================================================================


def random_filename():
    return nshash(unixtime_str())

#=============================================================================

# The is a temporary fudge ...

def is_ancestor(entity_hrns, ancestor_id):
    # This version works only within the same constraints as "omtrad" mode
    # (i.e. UTF-8 Latin character set for HRNS).
    ancestor_fph, ancestor_hrns, etype, m = identify_entity(ancestor_id)
    a = ancestor_hrns.split(NSS)
    e = entity_hrns.split(NSS)
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


# Alternative version ...

#def is_ancestor(entity_id, ancestor_id):
def _is_ancestor(entity_id, ancestor_id):
    # This version uses the  get_parent( )  function.
    e_fph, e_hrns, etypes, m = identify_entity(entity_id)
    if not e_fph:
        return False
    a_fph, a_hrns, etypes, m = identify_entity(ancestor_id)
#    if not a_fph:
#        return False
    # Whether or not it has been registered as an identifier, an empty list is
    # returned if ancestor_id does not identify a *namespace*:
    if not ("namespace" in etypes):
        return False
    # Every identifier has a parent so this is a sufficient start ...
    parent_fph = get_parent(e_fph)
    # ... from which to burrow down into the ancestral depths until ...
    while parent_fph:
        parent_fph = get_parent(parent_fph)
        if parent_fph == a_fph:
            # ... either the tentative ancestor has been found in the chain or
            return True
    else:
        # ... the tentative ancestor has not been found anywhere in the chain.
        return False



def is_in_private_namespace(entity_hrns, pn_id):
    pn_fph, pn_hrns, etype, m = identify_entity(pn_id)
    return is_ancestor(entity_hrns, pn_hrns) or (entity_hrns == pn_hrns)



#=============================================================================

def retrieve_pmap(owner_id):
    owner_fph, owner_hrns, etypes, m = identify_entity(owner_id)
    if not owner_fph:
#        print("retrieve_pmap: " + owner_fph + " is not registered")
        return {}, owner_id + " is not registered"
    if not ("primid" in etypes):
#        print("retrieve_pmap: " + owner_id + " is not a primid")
        return {}, owner_id + " is not a primid"
#    print("pmap owner: " + owner_fph + " > " + owner_hrns)

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
#        print("retrieve_pmap: no pmap for " + owner_hrns + " (a)")
#        return {}, ""
        return {}, "retrieve_pmap: no pmap for " + owner_hrns
    #elif isinstance(result, tuple) and (result[0] is None):
    elif result[0] is None:
#        print("retrieve_pmap: no pmap for " + owner_hrns + " (b)")
        return {}, ""
    else:
        pmap = pickle.loads(result[0])
#        print("retrieve_pmap: pmap for " + owner_hrns + " :")
#        print(pmap)
        return pmap, ""     # dictionary of  ahid_hrns:currency_hrns
                            # pairs for display in table.

#=============================================================================

def new_pairing(
        primid_id,      # *primid* (HRNS or FPH, and must exist already)
        ahid_hrns,      # *ahid* - must use HRNS because may not exist yet
        currency_id     # *currency* (HRNS or FPH, and must exist already)
    ):
    # The *currency* and owner *primid* are validated before proceeding to
    # create a new *ahid* (*account-holder identity*. Only if both exist will a
    # new *account* or *ahid* be created.
    currency_fph, currency_hrns, cetypes, m = identify_entity(currency_id)
#    if m:
#        print("identify_entity(currency_id): " + m)
    if not currency_fph:
        return "", currency_id + " is not a registered identifier (12)"
    if not ("currency" in cetypes):
        return "", currency_hrns + " is not a currency"
    primid_fph, primid_hrns, petypes, m = identify_entity(primid_id)
#    if m:
#        print("identify_entity(primid_id)" + m)
    if not primid_fph:
        return "", "", primid_id + " is not a registered identifier (13)"
    if not ("primid" in petypes):
        return "", "", primid_hrns + " is not a primid"
    # If the *ahid* does not exist already it must be created:
    r_ahid_fph, r_ahid_hrns, etypes, m = identify_entity(ahid_hrns)
    if not ("ahid" in etypes):
        # A new *ahid* is created:
        ahid_name, parent_hrns = split_hrns(ahid_hrns)
        ahid_fph, ahid_hrns, \
        m = new_ahid(ahid_name, parent_hrns, primid_fph)
#        print("new pairing: new ahid = " + ahid_fph + " > " + ahid_hrns)
    else:
        ahid_fph = r_ahid_fph
        ahid_hrns = r_ahid_hrns
#        print("new pairing: retrieved ahid = " + ahid_fph + " > " + ahid_hrns)
    # At this point, whether or not it has been necessary to create it, we now
    # have both the HRNS and the FPH of the *ahid*. It can now be paired with
    # the specified *currency* to index a new *account*.
    # The *account* created for this *ahid"|*currency* pairing will not usually
    # be seen by its owner, but it still needs an HRNS - both in order to be
    # able to assign it an FPH and to insure that it is both unique and easily
    # related to the two components of the pairing. Therefore its name is (by)
    # default) constructed from the two paired HRNS:
    #
    ah_id = "^".join(ahid_hrns.split(NSS))
    c_id = "^".join(currency_hrns.split(NSS))
    account_name = "_".join(["", ah_id, "&", c_id, ""])
    #
    # This name is then prefixed to the root of the owner *primid*'s private
    # *namespace*.
    account_fph, account_hrns, \
    m = new_account(account_name, primid_id, ahid_fph, currency_fph)
    #
    # The *ahid* may be paired with any *currency* (once only). These
    # serve as the co-ordinates in a grid identifying the *account* created
    # above.
    #
    # If a *pairing* entity does not exist already it is created.
    #
    # The pairings dictionary is retrieved:
    pmap, m = retrieve_pmap(primid_fph)
    if pmap is None:
        pmap = {}
    if not (ahid_hrns in pmap.keys()):
        pmap[ahid_hrns] = {}
    if not (currency_hrns in pmap[ahid_hrns].keys()):
        pmap[ahid_hrns][currency_hrns] = account_fph
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Update the pmap:
        cursor.execute(
            "UPDATE primids SET pmap = ? WHERE entity_fph = ?",
            (pickle.dumps(pmap), primid_fph)
        )
        # Update the *ahid*s list:
        cursor.execute(
            "SELECT ahids_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        if (result is None) or (result[0] is None):
#            print("new pairing: ahids_fph_list not found")
            ahids_fph_list = []
        else:
            ahids_fph_list = pickle.loads(result[0])
        if not (ahid_fph in ahids_fph_list):
            ahids_fph_list.append(ahid_fph)
            cursor.execute(
                "UPDATE primids SET ahids_fph_list = ? WHERE entity_fph = ?",
                (pickle.dumps(ahids_fph_list), primid_fph)
            )
            conn.commit()
        cursor.close()










    return account_fph, account_hrns, ""

#=============================================================================

def list_primid_ahids(primid_fph):





    return ahids_list





#=============================================================================

def retrieve_pairing_account_fph(ahid_id, currency_id):
#    print("retrieving pairing account: ", end="")
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_id)
#    print("ahid: " + ahid_fph + " > " + ahid_hrns)
    if not ahid_fph:
        return "", "", ahid_id + " is not a registered identifier (1)"
    if not ("ahid" in etypes):
        return "", "", ahid_hrns + " is not an account-holder"
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not currency_fph:
        return "", "", currency_id + " is not a registered identifier (2)"
    if not ("currency" in etypes):
        return "", "", currency_fph + " is not a currency"

#    print("ahid = " + ahid_hrns + " and currency = " + currency_hrns)

    primid_fph = get_ahid_primid(ahid_fph)
#    print("primid (1) = " + primid_fph + " > " + fph_to_hrns(primid_fph))

    primid_fph, primid_hrns, etypes, m = identify_entity(primid_fph)
#    print("primid (2) = " + primid_fph + " > " + fph_to_hrns(primid_fph))
    if not primid_fph:
        return "", "", primid_fph + " is not a registered identifier (3a)"
#    if primid_fph:
#        pmap, m = retrieve_pmap(primid_fph)
#    else:
#        return "", "", "Unable to retrieve pmap for ahid " + ahid_hrns
    pmap, m = retrieve_pmap(primid_fph)

#    print("pmap: ", end="")
#    print(pmap)
#    print("pmap.keys(): ", end="")
#    print(pmap.keys())
#    print("ahid_hrns = " + ahid_hrns)
    if not (ahid_hrns in pmap.keys()):
#        print(ahid_hrns + " is not in pmap.keys()")
        return "", "", ahid_hrns + " is not in pmap.keys()"
#    print(pmap[ahid_hrns].keys())
    if not (currency_hrns in pmap[ahid_hrns].keys()):
        return "", "", ahid_hrns + " is not in ahid|currency pairing"
    currencies_available = pmap[ahid_hrns]
    if not (currency_hrns in pmap[ahid_hrns].keys()):
        return "", "", ahid_hrns + " does not use currency " + currency_hrns
    account_fph = pmap[ahid_hrns][currency_hrns]
    account_fph, account_hrns, etypes, m = identify_entity(account_fph)
    if not account_fph:
        return "", "", account_id + " is not a registered identifier"
    if m:
        return "", "", m
    elif not ("account" in etypes):
        return "", "", "Error: entity is not account" # should be impossible
    return account_fph, primid_fph, ""

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
    parent_fph = ""
    while not parent_fph:
        parent_fph, parent_hrns, etype, m = identify_entity(parent_hrns_)
        name, parent_hrns = split_hrns(parent_hrns_)
        chain_links.append(name)
        parent_hrns_ = parent_hrns
    ns_fph = parent_fph
    chain_links.pop()
    while len(chain_links) > 0:
        ns_name = chain_links.pop()
        ns_fph, ns_hrns, m = new_namespace(ns_name, ns_fph, c_fph, s_fph)
    return ns_fph

#==============================================================================



#def create_import_currency(currency_hrns, steward_fph):
#    if not re_hrns.match(currency_hrns):
#        return "", "", currency_hrns + " is invalid HRNS"
#    steward_fph, m = hrns_to_fph("adm.cc")
#    currency_fph, currency_hrns, etype, m = identify_entity(currency_hrns)
#    if currency_fph: # the entity exists already
#        return currency_fph, currency_hrns, currency_hrns + " exists already"
#    name, parent_hrns = split_hrns(currency_hrns)
#    parent_fph = complete_parent_namespace(parent_hrns)
#    currency_fph, currency_hrns, \
#    m = new_currency(
#            name,
#            parent_fph,
#            steward_fph,
#            "",
#            "",
#            name
#        )
#    return currency_fph, currency_hrns, ""
