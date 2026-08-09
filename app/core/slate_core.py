import sqlite3
import random
import os
import pickle
from pathlib import Path
from string import ascii_lowercase

from app.core.constants import DB_DIR, DB_BKP_DIR
from app.core.constants import IDENTIFIERS_DB, ENTITIES_DB, PAYMENTS_DB
from app.core.constants import HUBS_DB
from app.core.constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from app.core.constants import SUBSTRATE_FPH
from app.core.constants import VERSION, CONFIG
from app.core.constants import NSS # NamseSpace Separator character

from app.core.configdb import get_config

from app.core.common import filename_timestamp as timestamp
from app.core.common import ledger_timestamp
from app.core.common import nshash
from app.core.common import unixtime_str

from app.core.display import integer_to_money_format

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from app.core.fph_hrns_maps import delete_fph_from_map

from app.core.dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from app.core.dbm_functions import dbm_create_map

from app.core.auth import auth_hash, check_auth_hash, generate_access_token

from app.core.regexp_list import *

from app.core.unix_functions import fcopy

from app.core.cctld_list import *

from app.core.logging import log_event

#------------------------------------------------------------------------------

def create_db(dbpath):
    if os.path.exists(dbpath):
        # If the database exists already, it is deleted after a time-stamped
        # copy has been saved.
        os.remove(dbpath)
        # create or open DB (this creates the file if it doesn't exist)
    conn = sqlite3.connect(dbpath)
    conn.execute("PRAGMA user_version;")
    conn.close()
    # set permissions to 660 (rw-rw----)
    os.chmod(dbpath, 0o660)

#==============================================================================
def create_hubs_db():

    # This database is kept separate from the others because it needs to be
    # kept consistent with copies held across other hubs (according to rules
    # not yet defined):

#    if os.path.exists(HUBS_DB):
#        # If the database exists already, it is deleted after a time-stamped
#        # copy has been saved.
#        os.remove(HUBS_DB)
#        # create or open DB (this creates the file if it doesn't exist)
#    conn = sqlite3.connect(HUBS_DB)
#    conn.execute("PRAGMA user_version;")
#    conn.close()
#    # set permissions to 660 (rw-rw----)
#    os.chmod(HUBS_DB, 0o660)

    create_db(HUBS_DB)

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

def _get_hub_mode():
#def get_hub_mode():
    hub_mode = os.environ.get("HUB_MODE")
    if hub_mode is None:
        return "slate"
    elif hub_mode in ["slate", "nests"]:
        return hub_mode
    else:
        return "slate"

# Get version number:
def get_version():
    with open(VERSION, "r") as v_file:
        version = v_file.read()
    return version

#==============================================================================
#
def get_hub_mode():
    return "slate"    # TEMPORARY FUDGE!
#    return get_config("hub_mode")

#==============================================================================

def get_parent(entity_fph):
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT parent_fph FROM entities_registered WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None: # assume "public" *namespace* (FPH = "")
        return ""
    elif result[0] is None:
        return ""
    else:
        return result[0]


def record_parent(id_fph, parent_fph):
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE entities_registered SET parent_fph = ? " \
            + "WHERE entity_fph = ?",
            (parent_fph, id_fph)
        )
        conn.commit()
        cursor.close()


def get_private_namespace_root(entity_fph):
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT pnsr_fph FROM entities_registered WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None: # assume "public" *namespace* (FPH = "")
        return ""
    elif result[0] is None:
        return ""
    else:
        return result[0]


def record_private_namespace_root(id_fph, private_namespace_root_fph):
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE entities_registered SET pnsr_fph = ? WHERE entity_fph = ?",
            (private_namespace_root_fph, id_fph)
        )
        conn.commit()
        cursor.close()


def is_in_active_tree(entity_id):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    in_active_tree = True
    parent_fph = get_parent(entity_fph)
    while parent_fph: # FPH of SUBSTRATE is "", which is its own parent.
        if not is_active(parent_fph):
            in_active_tree = False
            break
    return in_active_tree




#==============================================================================
## Choose the working database file for the *namespace*:

def select_db_filepath(db_name, owner_fph):
    # Is the database name valid?
    if not (db_name in ["entities", "payments"]):
        return ""
    # If the PNSR (FPH) has been provided, assume public namespace.
    if isinstance(owner_fph, str) and re_fph.match(owner_fph):
        DB = DB_DIR + owner_fph + "_" + db_name + ".db"
    else:
        DB = DB_DIR + db_name + ".db"
    return DB

# REPLACE the above with ...

def select_entities_db_filepath(entity_fph):
    pnsr = get_private_namespace_root(entity_fph)
    # If the PNSR (FPH) has been provided, assume public *namespace*.
    if isinstance(pnsr_fph, str) and re_fph.match(pnsr_fph):
        DB = DB_DIR + owner_fph + "_entities.db"
    else:
        DB = DB_DIR + "_entities.db"
    return DB

# The following presents a problem.
# During a bulk import, this may help to prevent lockout for other users when
# adjusting the balances, but payments.db is probably best kept as a shared
# journal. However, the bulk import payments recorded can be fed initially into
# a private PAYMENTS_DB before being drip-fed to the journal.

def select_payments_db_filepath(entity_fph):
    pnsr = get_private_namespace_root(entity_fph)
    # If the PNSR (FPH) has been provided, assume public *namespace*.
    if isinstance(pnsr_fph, str) and re_fph.match(pnsr_fph):
        DB = DB_DIR + owner_fph + "_payments.db"
    else:
        DB = DB_DIR + "_payments.db"
    return DB

#==============================================================================
## Create the SQLite indentifiers database

def create_identifiers_db():

    if os.path.exists(IDENTIFIERS_DB):
        # If the database exists already, it is deleted.
        os.remove(IDENTIFIERS_DB)
    # create or open DB (this creates the file if it doesn't exist)
    conn = sqlite3.connect(IDENTIFIERS_DB)
    conn.execute("PRAGMA user_version;")
    conn.close()
    # set permissions to 660 (rw-rw----)
    os.chmod(IDENTIFIERS_DB, 0o660)

    with sqlite3.connect(IDENTIFIERS_DB) as conn:
        cursor = conn.cursor()
        # 2025-10-08: Added PNSR (Private Namespace Root) field
        #
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS entities_registered (" \
            + "entity_fph TEXT PRIMARY KEY, " \
            + "parent_fph TEXT, " \
            + "pnsr_fph TEXT, " \
            + "namespace INTEGER NOT NULL DEFAULT 0, " \
            + "currency INTEGER NOT NULL DEFAULT 0, " \
            + "account INTEGER NOT NULL DEFAULT 0, " \
            + "primid INTEGER NOT NULL DEFAULT 0, " \
            + "ahid INTEGER NOT NULL DEFAULT 0" \
            + ");"
        )
        conn.commit()
        cursor.close()

#==============================================================================
## Create the SQLite entities database

def create_entities_db(owner_fph):

    ENTITIES_DB = select_db_filepath("entities", owner_fph)

    print("ENTITIES_DB_ = " + ENTITIES_DB)

    if os.path.exists(ENTITIES_DB):
        # If the database exists already, it is deleted.
        os.remove(ENTITIES_DB)
    #
    # create or open DB (this creates the file if it doesn't exist)
    conn = sqlite3.connect(ENTITIES_DB)
    conn.execute("PRAGMA user_version;")
    conn.close()
    # set permissions to 660 (rw-rw----)
    os.chmod(ENTITIES_DB, 0o660)

    # If this entity is a *private namespace* (one that shares an identifier
    # with a *primid* or an *ahid*, or which has ramified from such a
    # *namespace*:
    # (1) It is owned by a *primid*, whether directly or indirectly via an
    #     *ahid*.
    # (2) It is either active (in which case all the usual operations are
    #     possible) or inactive (in which case only its owner or stewards can
    #     perform any actions on it).
    # (3) If it is identified as a "sandbox" *namespace*, its contents may be
    #     cleared or otherwise changed by its owner or stewards.
    # (4) If is private, all operations upon or within it happen only with the
    #     authorization of its owner|stewards.
    # (5) If it is marked as "open", a new user can register its *primary
    #     identity) within it.
    # (6) When a *namespace* is created, its initial ownership is inherited
    #     from its parent *namespace*.
    # That ownership is not the same as a stewardship. If a *namespace* has an
    # owner it needs no stewards and, if it is an *identity* serving as the
    # root *namespace* of such a tree it cannot have stewards, but *namespaces*
    # created as children/descendants of such a root may have stewards if the
    # owner chooses to invite them.

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Create *namespace* table:
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS namespaces (" \
            + "entity_fph TEXT PRIMARY KEY, " \
            + "active INTEGER NOT NULL DEFAULT 1, " \
            + "open INTEGER NOT NULL DEFAULT 1, " \
            + "private INTEGER NOT NULL DEFAULT 0, " \
            + "sandbox INTEGER NOT NULL DEFAULT 0, " \
            + "default_currency_fph TEXT DEFAULT '', " \
            + "reg_currencies_listed INTEGER NOT NULL DEFAULT 0, " \
            + "reg_currencies_list BLOB, " \
            + "owner_fph TEXT DEFAULT '', " \
            + "stewards_fph_list BLOB" \
            + ");"
        )

        # NB, since a *primid* or *ahid* can serve as the root private
        # *namespace*, a default *currency* must be specified. This has the
        # same identifier as this *primid* initially but may be changed
        # subsequently should the need arise.
        #
        # Since v.0.2, the same identifier can serve for one instance of each
        # of the following entity types:
        #   *primid*    -- a.k.a. *login identity* - unique agent identifier
        #   *ahid*      -- pairing *identity*
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
            + "ahids_fph_list BLOB, " \
            + "accounts_fph_list BLOB, " \
            + "pmap BLOB, " \
            + "nstewardships_fph_list BLOB, " \
            + "cstewardships_fph_list BLOB, " \
            + "password_hash BLOB NOT NULL, " \
            + "pin TEXT, " \
            + "access_token_hash BLOB, " \
            + "administrator INTEGER NOT NULL DEFAULT 0, " \
            + "registry_namesapce TEXT, " \
            + "initial_currency TEXT, " \
            + "one_identity INTEGER NOT NULL DEFAULT 1, " \
            + "one_currency INTEGER NOT NULL DEFAULT 1" \
            + ");"
        )
        #
        # 2026-03-30 The following four tables have been added:
        #
        #   registry_namesapce  FPH         The *namespace* in which this
        #                                   *primid* has been registered.
        #
        #   initial_currency    FPH         The initial *currency* for which
        #                                   this *primid* has been registered.
        #
        #   one_identity        boolean     This agent has only one *identity*.
        #
        #   one_currency        boolean     This agent has only one *currency*.
        #
        # These have been added to allow suppression (masking) of the ancestor
        # identifier string for neophytes having only one of each.
        #
        #----------------------------------------------------------------------
        # Create *ahids* (*account-holder identities*) table:
        #
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS ahids (" \
            + "entity_fph TEXT, " \
            + "primid_fph TEXT, " \
            + "accounts_fph_list BLOB, " \
            + "robot INTEGER NOT NULL DEFAULT 0, " \
            + "active INTEGER NOT NULL DEFAULT 1" \
            + ");"
        )
        # Create *currencies* table:
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
            + "open INTEGER NOT NULL DEFAULT 1, " \
            + "private INTEGER NOT NULL DEFAULT 0, " \
            + "currency_prefix TEXT, " \
            + "currency_suffix TEXT, " \
            + "default_account_name TEXT DEFAULT 'local', " \
            + "stewards_fph_list BLOB, " \
            + "sandbox INTEGER NOT NULL DEFAULT 0, " \
            + "type TEXT DEFAULT 'scalar', " \
            + "category TEXT DEFAULT 'money', " \
            + "units TEXT DEFAULT 'unspecified', " \
            + "metrical_equivalence DEFAULT 'unspecified', " \
            + "dimensions TEXT DEFAULT 'unspecified'" \
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
            + "account_type TEXT DEFAULT 'scalar', " \
            + "account_category TEXT DEFAULT 'money', " \
            + "account_units TEXT DEFAULT 'unspecified', " \
            + "account_metrical_equivalence 'lt', " \
            + "account_dimensions TEXT DEFAULT 'unspecified', " \
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
    name, parent_hrns = split_hrns(identifier_hrns)
    parent_fph, m = hrns_to_fph(parent_hrns)
    identifier_fph, m = hrns_to_fph(identifier_hrns)
    if m:
        delete_fph_from_map(identifier_fph)
        return ""

    # NB The HRNS:FPH pair are added to the HRNS<>FPH map, but the FPH will be
    #    added to the  identifiers.entities_registered  table only if the
    #    parent is already registered there.

    # The parent *namespace* FPH is registered in the child.parent map:

    # Every identifier has both a parent *namespace* (its immediate ancestor)
    # and a private *namespace* root (PNSR), the most recent ancestral
    # *namespace* sharing the identifier of a *primid*. The PNSR is mapped from
    # the identifier, either as an FPH (where the identifier sits within a
    # private *namespace*) or as an empty string (where the identifier sits
    # within the public *namespace*)
    #
    # Descendants of an identifer in a private *namespace* may be in either the
    # public *namespace* or in a different private *namespace*).
    #
    # Whenever a new identifier is registered, the PNSR is et to that of its
    # parent *namespace*. If a *primid* is subsequntly registered to that
    # identifier, its PNSR is overwritten with the FPH of its identifier.

    # An entry is created for this FPH in the [entities_registered] table if
    # its parent exists and only if it does not exist already.
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
        cursor = conn.cursor()
        # Identify the PNSR:
        cursor.execute(
            "SELECT pnsr_fph FROM entities_registered WHERE entity_fph = ?",
            (parent_fph,)
        )
        result = cursor.fetchone()
        if result is None: # assume "global public" *namespace* (FPH = "")
            pnsr_fph = ""
        elif result[0] is None:
            pnsr_fph = ""
        else:
            pnsr_fph = result[0]
        # Does the identifier exist already?
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (identifier_fph,)
        )
        result = cursor.fetchone()
        # If not ...
        if result is None:
            # Initially, no entity type is registered for this identifier:
            cursor.execute(
                "INSERT INTO entities_registered (" \
                + "entity_fph, parent_fph, pnsr_fph, " \
                + "namespace, currency, account, primid, ahid" \
                + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (identifier_fph, parent_fph, pnsr_fph, 0, 0, 0, 0, 0)
            )
            conn.commit()
        cursor.close()
    return identifier_fph

#==============================================================================
## Is the identifier registered?

## NB: This will require a separate database given that the ENTITIES_DB is
##     now going to be divided such that private *namespace*s sit alongside the
##     public *namespace*.

def identifier_unregistered(identifier_id):
    if re_hrns.match(identifier_id):
        # nshash( ) is used here because using  hrns_to_fph( ) would add to the
        # HRNS>FPH and FPH>HRNS maps.
        identifier_fph = nshash(identifier_id)
    elif re_fph.match(identifier_fph):
        identifier_fph = identifier_id
    else:
        return True
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
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
    return register_identifier(identifier_hrns)
    return identifier_fph, ""

#==============================================================================
## Get the list of *entity* types registered for a specified FPH::

def get_entity_types(entity_fph):
    if not re_fph.match(entity_fph):
        return [], "Invalid FPH: " + entity_fph
    entity_hrns = fph_to_hrns(entity_fph)
    if not entity_hrns:
        return [], ":: " + entity_fph + " is not a registered identifier"
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT " \
            + "namespace, " \
            + "currency, " \
            + "account, " \
            + "primid, " \
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
            entity_types.append("ahid")
        return entity_types, ""
    else:
#        entity_hrns = fph_to_hrns(entity_fph)
        return [], "No types registered for identifier " + entity_fph \
                   + " (" + entity_hrns + ")"
#        return [], ""

#=============================================================================
# Set, register or deregister an *entity* type for a specified identifier FPH:

def set_entity_type(identifier_id, entity_type, value):
    entity_fph, entity_hrns, etypes, m = identify_entity(identifier_id)
    if m:
        return m
    if not entity_fph:
        return "Identifier " + identifier_id + " is not registered"
    if entity_type in etypes:
        log_event(
            "activity",
            "registration",
            entity_type + " already registered for " + identifier_id
        )
        return ""
    # The valid entity types are:
    vetypes = ["namespace", "currency", "account", "primid", "ahid"]
    if not (entity_type in vetypes):
        return "Invalid entity type: " + entity_type
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
        cursor = conn.cursor()
        # Does [entities_registered] table contain an entry for this FPH?
        cursor.execute(
            "SELECT * FROM entities_registered WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            cursor.close()
            return "Identifier " + entity_fph + " is not registered"
        cursor.execute(
            "UPDATE entities_registered SET " + entity_type + " = ? " \
            + "WHERE entity_fph = ?", (int(value), entity_fph)
        )
        conn.commit()
        cursor.close()
    return ""

def register_full_entity_set(identifier_fph):
    if not re_fph.match(identifier_fph):
        return "Invalid FPH: " + identifier_fph
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
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
        cursor.execute(u, (identifier_fph,))
        conn.commit()
        cursor.close()
    return ""

def register_primid_entity_set(identifier_fph):
    # This is used when registering a new *primid*:
    if not re_fph.match(identifier_fph):
        return "Invalid FPH: " + identifier_fph
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
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
        # NB: Since this is registering a *primid*, its PNSR is also recorded.
        u = "UPDATE entities_registered SET " \
          + "namespace = 1, " \
          + "currency = 1, " \
          + "account = 1, " \
          + "primid = 1, " \
          + "ahid = 1 " \
          + "pnsr_fph, " \
          + "WHERE entity_fph = ?"
        cursor.execute(
            u, (identifier_fph,identifier_fph)
        )
        conn.commit()
        cursor.close()
    return ""

def register_general_entity_set(identifier_fph):
    # This is used when creating a new *namespace* or *currency*
    if not re_fph.match(identifier_fph):
        return "Invalid FPH: " + identifier_fph
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
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
    if entity_id == SUBSTRATE_FPH: # a unique exception
        return entity_id, "", list("namespace",), ""
    if re_fph.match(entity_id): # this is an FPH string?
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
        entity_hrns = entity_id
        entity_fph, m = hrns_to_fph(entity_id)
        if m: # something wrong here
            return "", "", [], m
        if entity_fph: # entity exists
            entity_types, m = get_entity_types(entity_fph)
            if m:
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
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
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
    if not (entity_type in ["account", "namespace", "ahid"]):
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
## List all *accounts* in the specified *currency*:

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
            account_fph = result[0]
            accounts.append(account_fph)
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
    # The *primid* cannot be created with an invalid username:
    if not re_slatename.match(username):
        errors += "Invalid name provided\n"
        return "", "", "", errors
    # The *primid* cannot be created with an invalid PIN:
    if not re_pin.match(pin):
        errors += "Invalid PIN provided\n"
        return "", "", "", errors
    # The *primid* cannot be created with an invalid parent *namespace*:
    parent_fph, parent_hrns, etypes, m = identify_entity(parent_id)
    if not parent_fph:
        errors += "Invalid parent\n"
        errors += m
        return "", "", "", m # parent is invalid
    # The *primid* can be created without a real name. If a real name is
    # provided it is used if and only if valid:
    if realname:
        if not re_realname.match(realname):
            errors += "Invalid real name \"" + realname + "\" discarded " \
                   + "so the primid has been created without a real name.\n"
            primid_realname = ""
    # The *primid* cannot be created if no valid primary email address has
    # been provided:
    if not email_address_1:
        delete_fph_from_map(primid_fph)
        errors += "No primary email address provided\n"
        return "", "", "", errors
    if not re_email.match(email_address_1):
        delete_fph_from_map(primid_fph)
        errors += "Invalid entry: primary email address\n"
        return "", "", "", errors
    # If an invalid secondary email address is provided it is discarded and the
    # *primid* is created with only a primary email address:
    if email_address_2:
        if not re_email.match(email_address_2):
            errors += "Invalid secondary email address " + email_address_2 \
                   + " has been discarded.\n"
            email_address_2 = ""
    # The authentication tokens are created automatically:
    access_token = generate_access_token()
    access_token_hash = auth_hash(access_token)

    # NB, when a new *primid* is created the following additional entities (of
    # which it will be the owner or a steward) are created and registered to
    # the same identifer:
    # - a *namespace* (the root of this *primid*s private *namesapce* tree)
    # - a *currency* (of which this *primid* will be the initial steward)
    # - an *ahid* (since any *primid* must serve also as an *ahid*)
    # - an *account* owned by this *primid*

    primid_hrns = username + NSS + parent_hrns
    if identifier_unregistered(primid_hrns):
        primid_fph = register_identifier(primid_hrns)
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_hrns)
    # If a *primid* is already registered to this identifier, it cannot be
    # be re-used for another.
    if ("primid" in etypes):
        errors += primid_hrns + " exists already (primid)\n"
        return "", "", "", errors
    # If control has reached this point, we can now register a *primid* for
    # this identifier:
    m = register_entity_type(primid_fph, "primid")
    if m:
        print(m)

    # The PNSR of this identifier is overwritten with its FPH because it has a
    # *primid* registered to it, making it the root of a private *namespace*
    # tree.
    record_private_namespace_root(primid_fph, primid_fph)

    # This *primid* will be the owner of a an *account* sharing the same
    # identifier, but it cannot be created at this point because the *primid*
    # has not yet been added to the primids table. The empty accounts list is
    # created here in preparation for that action in due course:
    accounts_fph_list = [] # REMOVE - obsolete

    ahid_hrns = currency_hrns = primid_hrns # lest we forget

    # This *primid* is the initial steward of a *namespace* and a *currency*
    # having the same FPH:
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
            + "pmap, " \
            + "nstewardships_fph_list, " \
            + "cstewardships_fph_list, " \
            + "password_hash, " \
            + "pin, " \
            + "access_token_hash" \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                primid_fph,
                realname,
                auth_hash(email_address_1),
                auth_hash(email_address_2),
                pickle.dumps({}),
                pickle.dumps(nstewardships_fph_list),
                pickle.dumps(cstewardships_fph_list),
                auth_hash(password),
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
            username,               # default account name
            account_type="scalar",
            category="money",
            units="unspecified",
            metrical_equivalence="lt",
            dimensions="unspecified"
        )
    #
    namespace_fph, namespace_hrns, \
    m = new_namespace(username, parent_fph, currency_fph, primid_fph, True)
    if m:
        print(m)
    # Although the *currency* has been created in order to prevent another
    # user from creating one with the same identifier, it is deactivated at
    # this point to prevent its display in the home page table:
#    m = deactivate_currency(currency_hrns, primid_hrns)

    # The new *ahid*|*currency* pairing-indexed *account* is created with this
    # *primid* as its owner, where the *ahid* shares the same identifier as the
    # *primid*:
    account_fph, account_hrns, \
    m = new_pairing(
            primid_fph,     # *ahid* belongs to *primid* and shares identifier;
            primid_hrns,    # *account* HRNS combines *ahid* & *currency*; and
            currency_fph    # *currency* was created immediately before this.
        )
    return primid_fph, primid_hrns, access_token, errors

# Although the initial access token is generated automatically here, it may be
# updated by the *primid* at any time.

#==============================================================================
## A new *ahid* is created:

### THIS may not be needed, given that in  new_pairing( )  a new *ahid*
###      entity is created directly.

def new_ahid(
        ahidname,
        parent_id,
        primid_id,
        robot=False     # If newly created, the *ahid* is made a robot.
    ):
    if not re_slatename.match(ahidname):
        return "", "", "Invalid name provided"
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if not primid_fph:
        return "", "", "The identifier " + primid_id + " is invalid"
    if not ("primid" in etypes):
        return "", "", "The identifier " + primid_hrns + " has no primid"
    parent_fph, parent_hrns, etypes, m = identify_entity(parent_id)
    if not parent_fph:
        return "", "", m # parent is invalid
    if not ("namespace" in etypes):
        return "", "", "Parent namespace not registered"
    ahid_hrns = ahidname + NSS + parent_hrns
    # Does this *ahid*'s identifier exist already?
    if identifier_unregistered(ahid_hrns):
        ahid_fph = register_identifier(ahid_hrns)
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_hrns)
    if not ("ahid" in etypes):
        m = register_entity_type(ahid_fph, "ahid")
        if m:
            print(m)
        with sqlite3.connect(ENTITIES_DB) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ahids (" \
                + "entity_fph, " \
                + "primid_fph, " \
                + "accounts_fph_list, " \
                + "robot, " \
                + "active" \
                + ") VALUES (?, ?, ?, ?, ?)",
                (ahid_fph, primid_fph, pickle.dumps([]), robot, 1)
            )
            conn.commit()
            cursor.close()
    if not ("namespace" in etypes):
        # If a new *namespace* is created here
        # (1) the *ahid*'s owner is assigned the initial stewardship, and
        # (2) it is assigned the default *currency* of its parent *namespace*.
        stewards_fph_list = []
        stewards_fph_list.append(primid_fph)
        active, open, sandbox, private, owner_fph, \
        currency_fph, stewards_list, \
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


def ahid_is_robot(ahid_id):
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_id)
    if not ahid_fph:
        return False
    if not ("ahid" in etypes):
        return False
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT robot FROM ahids WHERE entity_fph = ? ",
            (ahid_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return False
    if result[0]:
        return True
    else:
        return False


#==============================================================================
## A new *namespace* is created:

## TO DO:
## (1) Add "private" to the parameters list.
## (2) If the parent *namespace* is not within the specified _steward_'s
##     private *namespace* tree, check that it is _open_.


def new_namespace(nsname, parent_id, currency_id, steward_id, private=False):

    # The initial steward (*primid*) is validated:
    steward_fph, steward_hrns, etypes, m = identify_entity(steward_id)
    if not ("primid" in etypes):
        return "", "", steward_id + " is not a valid steward"

    # The initial *currency* is validated:
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not ("currency" in etypes):
        return "", "", currency_id + " is not a currency"

    if not re_slatename.match(nsname):
        return "", "", nsname + " is not a valid name"
    # The substrate is a special case of parent *namespace* (nameless). No
    # entity other than a *namespace* can be created with the substrate as its
    # parent.
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
    namespace_fph, namespace_hrns_, etypes, m = identify_entity(namespace_hrns)
#    if m:
#        print("::: m: " + m)
    # The *namespace* identifier must be registered if it does not exist already:
    if not namespace_fph:
        namespace_fph = register_identifier(namespace_hrns)

    # If this identifier already has a *namespace* associated with it, no
    # further action is required:
    if ("namespace" in etypes):
        return namespace_fph, namespace_hrns, ""

    m = register_entity_type(namespace_fph, "namespace")
    if m:
        print(m)
    ns_fph, ns_hrns, netypes, m = identify_entity(namespace_fph)
    if m:
        print(m)

    # TEMPORARY FUDGE (should not be needed) ##################################
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM namespaces WHERE entity_fph = ?", (namespace_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
        if not (result is None):
            return namespace_fph, namespace_hrns, ""
    ###########################################################################

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO namespaces (" \
            + "entity_fph, " \
            + "stewards_fph_list, " \
            + "default_currency_fph " \
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

# The version below was saved at 2026-05-21

def new_namespace_(
        nsname,
        parent_id,
        currency_id,
        steward_id,
        private=False
    ):
    if not re_slatename.match(nsname):
        return "", "", nsname + " is not a valid name"
    # The substrate is a special case of parent *namespace* (nameless). No
    # entity other than a *namespace* can be created with the substrate as its
    # parent.
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
    namespace_fph, namespace_hrns_, etypes, m = identify_entity(namespace_hrns)
    if not namespace_fph:
        # The *namespace* identifier is registered if it does not exist already:
        namespace_fph = register_identifier(namespace_hrns)
    elif "namespace" in etypes:
        # Otherwise, if a *namespace* is already registered for this identifier
        # not further action is required:
        return namespace_fph, namespace_hrns, ""
    steward_fph, steward_hrns, etypes, m = identify_entity(steward_id)
    if not ("primid" in etypes):
        return "", "", steward_id + " is not a valid steward"
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not ("currency" in etypes):
        return "", "", currency_id + " is not a currency"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM namespaces WHERE entity_fph = ?",
            (namespace_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            cursor.execute(
                "INSERT INTO namespaces (" \
                + "entity_fph, " \
                + "stewards_fph_list, " \
                + "default_currency_fph " \
                + ") VALUES (?, ?, ?)",
                (
                    namespace_fph,
                    pickle.dumps([steward_fph]),
                    currency_fph
                )
            )
            conn.commit()
            cursor.close()

        else:
            cursor.close()
            return namespace_fph, namespace_hrns, \
            namespace_hrns + " exists already (namespace)"

    # We can now register a *namespace* for this identifier:
    m = register_entity_type(namespace_fph, "namespace")
    if m:
        print(m)
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
    return namespace_fph, namespace_hrns, ""

#-------------------------------------------------------------------------------



#-------------------------------------------------------------------------------
# Build a chain of ancestor *namespaces* starting from the root *namespace* and
# all sharing the same in initial steward (usually, but not nessarily, the
# owner of the root *namespace*).
# The default *currency* is inherited from that of the root *namespace*.
def build_ancestor_chain(root_id, steward_id, *ns_list):
    root_fph, root_hrns, etypes, m = identify_entity(root_id)
    if m:
        return [], m
    if not ("namespace" in etypes):
        return [], root_id + " is not a namespace"
    parent_fph = root_fph
    steward_ph, steward_hrns, etypes, m = identify_entity(steward_id)
    if m:
        return [], m
    if not ("primid" in etypes):
        return [], steward_id + " is not a primid"
    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(parent_fph)
    if m:
        print(m)
        return [], m
    #
    # The initial steward must be one of those of the root *namespace*.
    if not (steward_id in stewards_list):
        return [], steward_hrns + " is not among those of the root namespace"
    ns_fph_list = []
    for ns_name in ns_list:
        # These intermediate *namespaces* are private to the root *namespace*'s
        # owner (the *primid* sharing its identifier).
        ns_fph, ns_hrns, \
        m = new_namespace(ns_name, parent_fph, currency_fph, steward_fph, True)
        if m:
            return [], m # exit early
        ns_fph_list.append(ns_fph)
    return ns_fph_list, "" # Return empty string if completed successfully.

#==============================================================================
## A new currency is added:

def new_currency(
        currency_name,
        parent_id,
        initial_steward_id,
        currency_prefix="",
        currency_suffix="",
        default_account_name="h",
        account_type="scalar",
        category="money",
        units="",
        metrical_equivalence="",
        dimensions=""
    ):
    initial_steward_fph, initial_steward_hrns, etypes, \
    m = identify_entity(initial_steward_id)
    if not initial_steward_fph:
        return "", "", initial_steward_id + " is not a registered identifier"
    if not ("primid" in etypes):
        return "", "", initial_steward_hrns + " has no primid registered"
    # The initial *account* in this *currency* is assigned to its initial
    # steward (which must exist already).
    parent_fph, parent_hrns, etypes, m = identify_entity(parent_id)
#    parent_fph, parent_hrns, etypes, m = identify_entity(parent_fph)
    if not parent_fph:
        return "", "", "Parent namespace does not exist"
    if not re_slatename.match(currency_name):
        return "", "", currency_name + " is not a valid name"
    # If no other name is specified, new *accounts* in this *currency* are
    # assigned this default name.
    if default_account_name:
        if not re_slatename.match(default_account_name):
            return "", "", default_account_name + " is not a valid name"
    if parent_hrns: # not SUBSTRATE
        currency_hrns = currency_name + NSS + parent_hrns # tentative HRNS
    else:
        currency_hrns = currency_name
    if identifier_unregistered(currency_hrns):
        currency_fph = register_identifier(currency_hrns)
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_hrns)
    if ("currency" in etypes):
        return "", "", "Currency " + currency_hrns + " is already registered"
    # If it does not exist, a new *namespace* is created with the same
    # identifier as the new *currency* (which is assigned as its default
    # *currency*) and having the same initial steward.
    if not ("namespace" in etypes):
        m = register_entity_type(currency_fph, "namespace")
        namespace_fph, namespace_hrns, \
        m = new_namespace(
                currency_name, parent_fph,  # identifier
                currency_fph,               # default *currency* for
                initial_steward_fph,        # initial steward
                False                       # This is a public *namespace*
            )
    m = register_entity_type(currency_fph, "currency")
    if m:
        print(m)
    # Now add *currency* specific properties:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO currencies (" \
            + "entity_fph, " \
            + "active, " \
            + "private, " \
            + "currency_prefix, " \
            + "currency_suffix, " \
            + "default_account_name, " \
            + "stewards_fph_list, " \
            + "sandbox, " \
            + "type, " \
            + "category, " \
            + "units, " \
            + "metrical_equivalence, " \
            + "dimensions" \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                currency_fph,
                1, # enabled
                0, # not private
                currency_prefix,
                currency_suffix,
                default_account_name,
                pickle.dumps([initial_steward_fph]),
                0, # not sandbox
                account_type,
                category,
                units,
                metrical_equivalence,
                dimensions
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
    return currency_fph, currency_hrns, ""


# Create a set of *currencies* from a list (of dictionaries). This might be
# used to create a list of community-/domain-specific *currencies*, e.g. for
# - real-time evaluation of presentations in a conferennce
# - wildlife surveys
# -
# Such a list can be associated with a registration *namespace* (such as that
# created for a community or conference) to allow the full set of *currencies*
# to be paired automatically with the new regsitrant in that *namespace*.
#
# (See create_pairings_from_list( ) function.)

def create_currencies_from_list(initial_steward_id, currency_list):
    errors = ""
    currencies_created_hrns = []
    currencies_created_fph = []
    steward_fph, steward_hrns, etypes, m = identify_entity(initial_steward_id)
    if m:
        errors += m + "\n"
        return [], [], m
    if not ("primid" in etypes):
        errors += "Invalid steward " + initial_steward_id
        return [], [], m
    for currency in currency_list: # list of dictionaries
        currency_name = currency["name"]
        parent_id = currency["parent"]
        steward_id = currency["steward"]
        prefix = currency["prefix"]
        suffix = currency["suffix"]
        default_account_name = currency["default_account_name"]
        account_type = currency["account_type"]
        category = currency["category"]
        units = currency["units"]
        metrical_equivalence = currency["metrical_equivalence"]
        dimensions = currency["dimensions"]
        #
        currency_fph, currency_hrns, \
        m = new_currency(
                currency_name, parent_id, initial_steward_id,
                prefix, suffix, default_account_name,
                account_type, category, units, metrical_equivalence, dimensions
            )
        if m:
           errors += m + "\n"
        elif currency_hrns:
            currencies_created_hrns.append(currency_hrns)
            currencies_created_fph.append(currency_fph)
        else:
            errors += "Unknown error\n"
    return currencies_created_fph, currencies_created_hrns, errors


def add_reg_currency_list_to_namespace(namespace_id, currency_list_fph):
    namespace_fph, namespace_hrns, etypes, m = identify_entity(namespace_id)
    if m:
        return m
    if not ("namespace" in etypes):
        return "No namespace registered for indentifier " + namespace_hrns
    currency_list_blob = pickle.dumps(currency_list_fph)
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE namespaces " \
            "SET reg_currencies_list = ?, reg_currencies_listed = ? " \
            "WHERE entity_fph = ?",
            (currency_list_blob, 1, namespace_fph)
        )
        conn.commit()
        cursor.close()
    return ""









#==============================================================================
## A new account is created in a specified currency:

def new_account(
        account_name, parent_id,    # identifier
        owner_id,                   # *ahid* or *primid*
        currency_id
    ):
    errors = ""
    parent_fph, parent_hrns, etypes, m = identify_entity(parent_id)
    if not parent_fph:
        return "", "", "Invalid parent FPH: " + parent_id
    # The *account* name may take either of two forms:
    # (1) that of a typical identifier (if  the *account* is for a "primid") or
    # (2) a form encoded automatically from the identifiers of an *ahid* and
    #     a *currency* (if  the *account* is for an "ahid"|*currency* pairing).
    account_for_primid = False
    account_for_pairing = False
    if re_slatename.match(account_name):
        account_for_primid = True
    elif re_pan1.match(account_name):
        pan = account_name.split("_&_")
        pan = account_name.split("&")
        pan_ahid = pan[0].replace("_", "")
        pan_currency = pan[0].replace("_", "")
        if (re_pan2.match(pan_ahid) and re_pan2.match(pan_currency)):
            account_for_pairing = True
    if not (account_for_primid or account_for_pairing):
        return "", "", "Invalid account name provided"
    account_hrns = account_name + NSS + parent_hrns
    if identifier_unregistered(account_hrns):
        account_fph = register_identifier(account_hrns)
    account_fph, account_hrns, etypes, m = identify_entity(account_hrns)
    if ("account" in etypes):
        # The identifier of an existing *account* cannot be used for another.
        return "", "", account_hrns + " exists already (account)"
    m = register_entity_type(account_fph, "account")
    if m:
        print(m)

    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not currency_fph:
        return "", "", currency_id + " is not a registered identifier"
    if not ("currency" in etypes):
        return "", "", currency_fph + " has no registered currency"
    currency_fph, currency_hrns, \
    active, open, private, sandbox, \
    currency_type, currency_category, currency_units, \
    currency_metrical_equivalence, currency_dimensions, \
    prefix, suffix, default_account_name, \
    stewards_list, m = get_currency_properties(currency_fph)
    if not open:
        return "", "", "Currency " + currency_hrns + " is not upon for use"
    if not re_slatename.match(account_name): # invalid *account* name provided
        account_name = default_account_name # from *currency*
    account_fph = register_identifier(account_hrns)
    m = register_entity_type(account_fph, "account")
    if m:
        print(m)
    # The owner may be either an *ahid* or a *primid".
    owner_fph, owner_hrns, etypes, m = identify_entity(owner_id)
    if not owner_fph:
        return "", "", "Invalid owner FPH: " + owner_fph
    if ("ahid" in etypes):
        table = "ahids"
    elif ("primid" in etypes):
        table = "primids"
    else:
        return "", "", owner_fph + " is not a valid agent type"
    # Now add *account* specific properties:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accounts (" \
            + "entity_fph, account_owner_fph, account_currency_fph, " \
            + "balance, volume, account_type, " \
            + "account_type, account_category, account_units, " \
            + "account_metrical_equivalence, account_dimensions" \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                account_fph, owner_fph, currency_fph, 0, 0, "money",
                currency_type, currency_category, currency_units,
                currency_metrical_equivalence, currency_dimensions
            )
        )
        conn.commit()
        cursor.execute(
            "SELECT accounts_fph_list FROM " + table + " WHERE entity_fph = ?",
            (owner_fph,)
        )
        result = cursor.fetchone()
        accounts_fph_list = pickle.loads(result[0])
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
    return account_fph, account_hrns, ""

#==============================================================================
##

def get_namespace_properties(namespace_id):
    namespace_fph, namespace_hrns, etypes, m = identify_entity(namespace_id)
#    print(namespace_hrns + " :: ", end="")
#    print(etypes)
    if m:
        return False, False, False, False, "", "", [], m
    # Is a *namespace* registered for this identifier?
    if not ("namespace" in etypes):
        return False, False, False, False, "", "", [], "Not a namespace"
    # Is at least one of the following types registered for this identifier?
#    if not (len(set(["primid", "ahid"]) & set(etypes)) > 0):
#        return False, "", "Entity cannot be a private namespace"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Add the stewarded entity's FPH to the *primid*'s stewardships list:
        cursor.execute(
            "SELECT active, open, sandbox, private, owner_fph, " \
            + "stewards_fph_list, default_currency_fph " \
            + "FROM namespaces WHERE entity_fph = ?", (namespace_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        m = "Namespace " + namespace_fph + " not found"
        return False, False, False, False, "", "", [], m
    else:
        active = bool(result[0])
        open = bool(result[1])
        sandbox = bool(result[2])
        private = bool(result[3])
        owner_fph = result[4]
        stewards_fph_blob = result[5]
        currency_fph = result[6]
        stewards_list = pickle.loads(stewards_fph_blob)
    return active, open, sandbox, private, \
           owner_fph, currency_fph, stewards_list, ""

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
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
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
        return entity_hrns + " is not a namespace type"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT default_currency_fph FROM namespaces " \
            + "WHERE entity_fph = ?", (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return "Default currency cannot be identified"
    else:
        return result[0]

#==============================================================================
##

def get_currency_properties(currency_id):
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if m:
        return "", "", \
               False, False, False, False, \
               "", "", "", "", "", \
               "", "", "", \
               [], m
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT active, private, open, sandbox, " \
            + "type, category, units, metrical_equivalence, dimensions, " \
            + "currency_prefix, currency_suffix, default_account_name, " \
            + "stewards_fph_list FROM currencies WHERE entity_fph = ?",
            (currency_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        m = "Currency " + fph_to_hrns(currency_fph) + " not found"
        return "", "", \
               False, False, False, False, \
               "", "", "", "", "", \
               "", "", "", \
               [], m
    #
    active = bool(result[0])
    private = bool(result[1])
    open = bool(result[2])
    sandbox = bool(result[3])
    type = result[4]
    category = result[5]
    units = result[6]
    metrical_equivalence = result[7]
    dimensions = result[8]
    prefix = result[9]
    suffix = result[10]
    default_account_name = result[11]
    stewards_fph_blob = result[12]
    stewards_list = pickle.loads(stewards_fph_blob)
    return currency_fph, currency_hrns, \
           active, open, private, sandbox, \
           type, category, units, metrical_equivalence, dimensions, \
           prefix, suffix, default_account_name, \
           stewards_list, ""

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
# This will list all *accounts* belonging to an *ahid* or "primid", the
# *account* itself identifying its *currency*.

def list_accounts(identity_id, identity_etype):
    identity_fph, identity_hrns, etypes, m = identify_entity(identity_id)
    if not identity_fph:
        return [], identity_id + " is not a registered identifier (3)"
    if not (identity_etype in etypes): # *ahid* or *primid*
        return [], identity_hrns + " has no registered " + identity_etype
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT accounts_fph_list FROM " + identity_etype + "s " \
            + "WHERE entity_fph = ?", (identity_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            accounts_fph_blob = pickle.dumps([])
            cursor.execute(
                "UPDATE " + identity_etype + "s SET accounts_fph_list = ? " \
                + "WHERE entity_fph = ?", (accounts_fph_blob, identity_fph)
            )
            conn.commit()
            cursor.close()
            return [], identity_hrns + " has no accounts."
        else:
            cursor.close()
            accounts_fph_list = pickle.loads(result[0])
    return accounts_fph_list, ""

#==============================================================================
## List the *identity*'s *accounts* in a specified *currency*:
#
# This will list all *accounts* in a specified *currency* belonging to a
# *primid*, *ahid* or "primid".

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
## List the *primid*'s accounts: #

def list_primid_accounts(primid_fph):
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT accounts_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        if result is None:
#            accounts_fph_list = []
#            accounts_fph_blob = pickle.dumps(accounts_fph_list)
            accounts_fph_blob = pickle.dumps([])
            cursor.execute(
                "UPDATE primids SET accounts_fph_list = ? WHERE entity_fph = ?",
                (accounts_fph_blob, primid_fph)
            )
            conn.commit()
            cursor.close()
            return [], "The primid " + primid_fph + " has no accounts."
        else:
            cursor.close()
#            accounts_fph_blob = result[0]
#            accounts_fph_list = pickle.loads(accounts_fph_blob)
            accounts_fph_list = pickle.loads(result[0])
        return accounts_fph_list, ""    # list + message

#==============================================================================
## List the *ahid*'s accounts: #

def list_ahid_accounts(ahid_fph):
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_fph)
    if not ahid_fph:
        return [], ahid_fph + " is not a registered identifier"
    if not ("ahid" in etypes):
        return [], "Ientifier " + ahid_hrns + " has no ahid registered"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT accounts_fph_list FROM ahids WHERE entity_fph = ?",
            (ahid_fph,)
        )
        result = cursor.fetchone()
        if result is None:
#            accounts_fph_list = []
#            accounts_fph_blob = pickle.dumps(accounts_fph_list)
            accounts_fph_blob = pickle.dumps([])
            cursor.execute(
                "UPDATE ahids SET accounts_fph_list = ? WHERE entity_fph = ?",
                (accounts_fph_blob, ahid_fph)
            )
            conn.commit()
            cursor.close()
            return [], "The ahid " + ahid_fph + " has no accounts."
        else:
            cursor.close()
#            accounts_fph_blob = result[0]
#            accounts_fph_list = pickle.loads(accounts_fph_blob)
            accounts_fph_list = pickle.loads(result[0])
        return accounts_fph_list, ""    # list + message

#==============================================================================
##
#
# NB  The two functions above may be combined into a single function:

#def list_agent_accounts(agent_fph, etype):
def list_agent_accounts(agent_fph):

    if entity_type_is_registered(agent_fph, "ahid"):
        accounts_fph_list, m = list_ahid_accounts(agent_fph)
        if m:
            return [], m
    elif entity_type_is_registered(agent_fph, "primid"):
        accounts_fph_list, m = list_primid_accounts(agent_fph)
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
# to the specified *currency*: UPDATE URGENTLY (2025-11-10)
#
# i.e. valid combinations for a specific identifier are:
#   | *primid* | *ahid*   |      *currency*|*ahid* -> *account*
#   |          | *ahid*   |      *currency*|*ahid* -> *account*
#
# The following combinations are also possible for a specific identifier:
#   | *primid* |          |      no *account*
#   | *primid* | *ahid*   |      *currency*|*ahid* -> *account*
#   |          | *ahid*   |      *currency*|*ahid* -> *account*
# The system will still function in these combinations, but they should never
# occur by design.
#
# Therefore,
# - *accounts* can still be held by a *primid*, but those are indexed directly
#   by an identifier rather than indirectly from a pairing
# - each *account* belongs to an *ahid* or a *primid*
# - each *account* is addressed either directly (by its own identifier) or
#   indirectly (by a pairing of *currency* and *ahid* identifiers)
# - each *account* identifies the *ahid* or *primid* to which it belongs
# - each *account* identifies its *currency*
# - each *currency* lists every *account* belonging to it
# - each *ahid* identifies the *primid* to which it belongs
# - each *primid* lists every *ahid* and *account* belonging to it
# - each *primid* lists every *currency* and *namespace* in its stewardship
# - each *primid* holds a *currency*|*ahid* pairing matrix indexing *account*

def list_id_accounts_in_currency(identity_id, identity_etype, currency_id):
    if not (identity_etype in ["ahid", "primid"]):
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

def list_primid_currencies(primid_fph): # in which a *primid* has accounts
    accounts_fph_list, m = list_primid_accounts(primid_fph)
    currencies_fph_list = []
    for account_fph in accounts_fph_list:
        currencies_fph_list.append(get_account_currency(account_fph))
    return currencies_fph_list




#==============================================================================
## List the *ahid*'s *account*s' *currencies*:
#
# For specified *ahid*, return a list the *currencies* in which it has an
# *account*

def list_ahid_currencies(ahid_fph):
    accounts_fph_list, m = list_ahid_accounts(ahid_fph)
    currencies_fph_list = []
    for account_fph in accounts_fph_list:
        currencies_fph_list.append(get_account_currency(account_fph))
    return currencies_fph_list

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
        # Retrieve the list of *ahids* for this *primid*:
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
        return "", "", 0, 0, False, "", "", "", "", "", \
               "No entity at " + account_id
    if not ("account" in etypes):
        return "", "", 0, 0, False, "", "", "", "", "", \
               "No account at " + account_hrns
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
            + "account_category, " \
            + "account_units, " \
            + "account_metrical_equivalence, " \
            + "account_dimensions, " \
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
        return "", "", 0, 0, False, "", "", "", "", "", "Account not found"
    # The owner of this *account* may be either an *ahid* or a *primid*.
    owner_fph, owner_hrns, etypes, m = identify_entity(result[0])
    if not (("ahid" in etypes) or ("primid" in etypes)):
        return "", "", 0, 0, False, "", "", "", "", "", \
               "Account  has no owner"
    currency_fph = result[1]
    balance = result[2]
    volume = result[3]
    active = bool(result[4])
    account_type = result[5]
    account_category = result[6]
    account_units = result[7]
    account_metrical_equivalence = result[8]
    account_dimensions = result[9]
    return currency_fph, owner_fph, balance, volume, active, \
           account_type, account_category, account_units, \
           account_metrical_equivalence, account_dimensions, ""


#==============================================================================
## Retrive the status of an account:

def account_status(account_fph):
    currency_fph, owner_fph, balance, volume, active, \
    account_type, account_category, account_units, \
    account_metrical_equivalence, account_dimensions, \
    m = get_account_properties(account_fph)
    exists = bool(currency_fph)
    if m:
        return False, False, "", "", 0, 0, m
    return exists, active, currency_fph, owner_fph, balance, volume, ""


#==============================================================================
## Sum the balances of *accounts* with similar properties:

def sum_account_balances(
        owner_id,
        account_category,
        account_units,
        account_metrical_equivalence,
        account_dimensions
    ):
    owner_fph, owner_hrns, etypes, m = identify_entity(owner_id)
    if not owner_fph:
        return {}, {}, owner_id + " is not a registered identifier"
    if not (("ahid" in etypes) or ("primid" in etypes)):
        return {}, {}, owner_hrns + " is not a registered ahid"

    print("category:              " + account_category)
    print("units:                 " + account_units)
    print("metrical_equivalence:  " + account_metrical_equivalence)
    print("dimensions:            " + account_dimensions)

    categories = ["money", "htime", "utime", "energy", "unspecified"]
    balance_sum = volume_sum = {}
    for c in categories:
        balance_sum[c] = volume_sum[c] = 0

    accounts_fph_list, m = list_accounts(owner_fph, "ahid")
    for account_fph in accounts_fph_list:
        print(fph_to_hrns(account_fph))
        currency_fph, owner_fph, balance, volume, active, \
        type, category, units, metrical_equivalence, dimensions, \
        m = get_account_properties(account_fph)
        print(category + " & " + account_category)
        if category == account_category:
            print("category match")
            balance_sum[category] += balance
            volume_sum[category] += volume
    return balance_sum, volume_sum, ""

#==============================================================================
##

def get_primid_properties(primid_id):
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if not primid_fph:
        return False, False, [], [], {}, [], [], \
               "No identifier registered for " + primid_id
    if not ("primid" in etypes):
        return False, False, [], [], {}, [], [], \
               "No primid registered for " + primid_id
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT " \
            + "active, " \
            + "administrator, " \
            + "ahids_fph_list, " \
            + "accounts_fph_list, " \
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
    if result[3] is not None:
        accounts_fph_list = pickle.loads(result[3])
    else:
        accounts_fph_list = []
    pmap = pickle.loads(result[4])
    nstewardships_fph_list = pickle.loads(result[5])
    cstewardships_fph_list = pickle.loads(result[6])
    return active, administrator, \
           ahids_fph_list, accounts_fph_list, pmap, \
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
        return False, "", [], "secid not found"
    active = bool(result[0])
    primid_fph = result[1]
    accounts_fph_list = pickle.loads(result[2])
    return active, primid_fph, accounts_fph_list, ""

def get_primid(ahid_id):
    active, primid_fph, accounts_fph_list, m = get_ahid_properties(ahid_id)
    return primid_fph

#------------------------------------------------------------------------------
# List stewards of a namespace or currency:

def list_stewards(entity_id, etype):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if not entity_fph:
        return [], entity_id + " is not a registered identifier"
    if not (etype in etypes):
        return [], entity_hrns + " has no registered " + etype
    if etype == "namespace":
        tbl = "namespaces"
    if etype == "currency":
        tbl = "currencies"
    select_str = "SELECT stewards_fph_list FROM " + tbl \
               + " WHERE entity_fph = ?"
    update_str = "UPDATE " + tbl \
               + " SET stewards_fph_list = ?" \
               + " WHERE entity_fph = ? (stewards_fph_list, entity_fph)"
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

def list_namespace_stewardships(primid_id):
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if m:
        return [], primid_id + " is not a registered identifier"
    if not ("primid" in etypes):
         return [], primid_id + " does not identify a primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nstewardships_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            nstewardships_fph_list = []
        else:
            nstewardships_fph_blob = result[0]
            nstewardships_fph_list = pickle.loads(nstewardships_fph_blob)
            if not (primid_fph in nstewardships_fph_list):
                # At the very least, the *primid* is a steward of the
                # *namespace* with which it shares an identifier:
                nstewardships_fph_list.append(primid_fph)
                nstewardships_fph_blob = pickle.dumps(nstewardships_fph_list)
                cursor.execute(
                    "UPDATE primids SET nstewardships_fph_list = ? " \
                    + "WHERE entity_fph = ?",
                    (nstewardships_fph_blob, primid_fph)
                )
                conn.commit()
        cursor.close()
    return nstewardships_fph_list, ""

#------------------------------------------------------------------------------
# List *currency* stewardships of a *primid*:

def list_currency_stewardships(primid_id):
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if not primid_fph:
        return [], primid_id + " is not a registered identifier"
    if not ("primid" in etypes):
        return [], primid_hrns + " has no primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cstewardships_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            cstewardships_fph_list = []
        else:
            cstewardships_fph_blob = result[0]
            cstewardships_fph_list = pickle.loads(cstewardships_fph_blob)
        # At the very least, the *primid* is a steward of the *currency* with
        # which it shares an identifier:
        if not (primid_fph in cstewardships_fph_list):
            cstewardships_fph_list.append(primid_fph)
        cstewardships_fph_blob = pickle.dumps(cstewardships_fph_list)
        cursor.execute(
            "UPDATE primids SET cstewardships_fph_list = ? " \
            + "WHERE entity_fph = ?",
            (cstewardships_fph_blob, primid_fph)
        )
        conn.commit()
        cursor.close()
    return cstewardships_fph_list, ""

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
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
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
        return  [], "" #

    namespace_fph_list = []
    for result in results:
        namespace_fph = result[0]
        if re_fph.match(namespace_fph):
            namespace_hrns = fph_to_hrns(namespace_fph)
            branch = namespace_hrns.replace(NSS + ancestor_hrns, "")
            if branch:
                namespace_fph_list.append(namespace_fph)

    return namespace_fph_list, ""


#==============================================================================

def get_ahid_primid(ahid_id):
    # (1) Each *ahid* belongs to one *primid*
    # (2) Each *primid* may have any number of *ahid*
    # (3) A *primid* may belong to itself as an *ahid*
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_id)
    if not ahid_fph:
        return ""
    if not ("ahid" in etypes):
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

    with sqlite3.connect(IDENTIFIERS_DB) as conn:
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
    namespace_fph, namespace_hrns, etypes, \
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
    parent_hrns = NSS.join(names).strip(NSS)
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
    if len(e) <= len(a):
        return False
    is_an_ancestor = True
    while len(a) > 0:
        if e.pop() != a.pop():
            is_an_ancestor = False
            break
    return is_an_ancestor

# ... used here primarily to determine whether the parent *namespace* for new
# entities is the private *namespace* of the importing *primid*.


# Alternative version ...

#def is_ancestor(entity_id, ancestor_id):
def _is_ancestor(entity_id, ancestor_id):
    # This version uses the  get_parent( )  function.
    e_fph, e_hrns, etypes, m = identify_entity(entity_id)
    if not e_fph:
        return False
    a_fph, a_hrns, etypes, m = identify_entity(ancestor_id)
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

#==============================================================================
# The pmap maps each *ahid*|*currency* pairs to an *account*. The pmap includes
# only *ahid*s belonging to the owner (*primid*).
#
# Currently, the *ahid* and *currency* are identified by their HRNS while the
# *account* is identified by its FPH.

def retrieve_pmap(owner_id):
    owner_fph, owner_hrns, etypes, m = identify_entity(owner_id)
    if not owner_fph:
        return {}, owner_id + " is not registered"
    if not ("primid" in etypes):
        return {}, owner_id + " is not a primid"
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
        return {}, "retrieve_pmap: no pmap for " + owner_hrns
    elif result[0] is None:
        return {}, ""
    else:
        pmap = pickle.loads(result[0])
        return pmap, "" # dictionary of *ahid*|*currency* pairs for display in
                        # the home page table.

#==============================================================================
# A new *ahid*|*currency* pairing is created:

def new_pairing(
        primid_id,      # *primid* (HRNS or FPH, and must exist already)
        ahid_hrns,      # *ahid* - must use HRNS because may not exist yet
        currency_id     # *currency* (HRNS or FPH, and must exist already)
    ):
    # The *currency* and owner *primid* are validated before proceeding to
    # create a new *ahid* (*account-holder identity*. Only if both exist will a
    # new *account* or *ahid* be created.
    currency_fph, currency_hrns, cetypes, m = identify_entity(currency_id)
    if not currency_fph:
        return "", currency_id + " is not a registered identifier (12)"
    if not ("currency" in cetypes):
        return "", currency_hrns + " is not a currency"
    primid_fph, primid_hrns, petypes, m = identify_entity(primid_id)
    if not primid_fph:
        return "", "", primid_id + " is not a registered identifier (13)"
    if not ("primid" in petypes):
        return "", "", primid_hrns + " is not a primid"
    # If the *ahid* does not exist already it must be created:
    r_ahid_fph, r_ahid_hrns, r_ahid_etypes, m = identify_entity(ahid_hrns)
    if m:
        print(m)
    if not ("ahid" in r_ahid_etypes):
        # A new *ahid* is created:
        ahid_name, parent_hrns = split_hrns(ahid_hrns)
        ahid_fph, ahid_hrns, m = new_ahid(ahid_name, parent_hrns, primid_fph)
        if not ("namespace" in r_ahid_etypes):
            # A new *namespace* is created
            # (a) sharing the parent *namespace* of the new *ahid*
            # (b) using the default *currency* of the parent as its own
            #parent_fph, m = hrns_to_fph(parent_hrns)
            parent_fph, parent_hrns, etypes, m = identify_entity(parent_hrns)
            if not parent_fph: # (should never happen)
                print("Panic! " + parent_hrns + " not a registered identifier")
            if not ("namespace" in etypes): # (should never happen)
                print("Panic! " + parent_hrns + " has no registered namespace")
            # The parent *namespace* details are retrieved:
            active, open, sandbox, private, owner_fph, \
            parent_currency_fph, stewards_list, \
            m = get_namespace_properties(parent_fph)
            # Its new child *namespace* is created
            namespace_fph, namespace_hrns, \
            m = new_namespace(
                    ahid_name,
                    get_parent(ahid_fph),
                    parent_currency_fph,    # The default *currency* inherited.
                    primid_fph,             # The *primid* is initial steward.
                    False                   # This is a public *namespace*.
                )
    else:
        ahid_fph = r_ahid_fph
        ahid_hrns = r_ahid_hrns
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



# Create a set of pairings between a specified *ahid* and each member of a list
# of *currencies*.
#
# Such a list would typically be found upon registration of a new *primid* from
# the registration *namespace*.
#
#
# (See create_currencies_from_list( ) function.)

def create_pairings_from_list(primid_id, ahid_hrns, currency_list):
    errors = ""
    invalid_currencies = ""
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if not ("primid" in etypes):
        errors += primid_id + " is not a primid\n"
        return errors, ""
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_hrns)
    if not ("ahid" in etypes):
        errors += ahid_id + " is not an ahid\n"
        return errors, ""
    for currency_id in currency_list:
        currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
        if m:
            errors += m + "\n"
            currency_list.remove(currency_id)
        elif not ("currency" in etypes):
            invalid_currencies += currency_hrns
            currency_list.remove(currency_id)
        else:
            account_fph, account_hrns, \
            m = new_pairing(primid_id, ahid_hrns, currency_id)
            if m:
                errors += m + "\n"
                currency_list.remove(currency_id)
    return errors, invalid_currencies







#=============================================================================

def list_primid_ahids(primid_id):
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if m:
        return []
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT ahids_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        if result is not None:
            ahids_list = pickle.loads(result[0])
        else:
            ahids_list = []
    return ahids_list

#=============================================================================

def retrieve_pairing_account_fph(ahid_id, currency_id):
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_id)
    if not ahid_fph:
        return "", "", ahid_id + " is not a registered identifier (1)"
    if not ("ahid" in etypes):
        return "", "", ahid_hrns + " is not an account-holder"
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not currency_fph:
        return "", "", currency_id + " is not a registered identifier (2)"
    if not ("currency" in etypes):
        return "", "", currency_fph + " is not a currency"
    primid_fph = get_ahid_primid(ahid_fph)
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_fph)
    if not primid_fph:
        return "", "", primid_fph + " is not a registered identifier (3a)"
    pmap, m = retrieve_pmap(primid_fph)
    if not (ahid_hrns in pmap.keys()):
        return "", "", ahid_hrns + " is not in pmap.keys()"
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

def complete_parent_namespace(identifier_hrns, primid_id):
    if primid_id == "":
        s_fph, m = hrns_to_fph("cc")
    else:
        s_fph, s_hrns, etype, m = identify_entity(primid_id)
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
        ns_fph, ns_hrns, \
        m = new_namespace(ns_name, ns_fph, c_fph, s_fph, False)
    return ns_fph

#==============================================================================
#

def set_activity_status_flag(entity_id, entity_type, active, steward_id):

    if entity_type == "namespace":
        table = "namespaces"
    elif entity_type == "currency":
        table = "currencies"
    else:
        return "Invalid type specified: must be a namespace or currency"

    if active:
        active_state = 1
    else:
        active_state = 0

    steward_fph, steward_hrns, p_etypes, m = identify_entity(steward_id)
    if not steward_fph:
        return steward_id + " is not a registered identifier"
    if not ("primid" in p_etypes):
        return "Identifier " + steward_hrns + " has no login identity"
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if not entity_fph:
        return entity_id + " is not a registered identifier"
    if not (entity_type in etypes):
        return "Identifier " + entity_hrns + " has no " + entity_type
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stewards_fph_list FROM " + table + " WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        if result is None: # (should never happen)
            cursor.close()
            return "The entity " + entity_hrns + " has no stewardships"
        stewards_fph_list = pickle.loads(result[0])
        if not (steward_fph in stewards_fph_list):
            cursor.close()
            return steward_hrns + " is not a steward of " + entity_hrns
        cursor.execute(
            "UPDATE " + table + " SET active = ? WHERE entity_fph = ?",
            (active_state, entity_fph)
        )
        conn.commit()
        cursor.close()
    return ""


def activate_currency(entity_id, steward_id):
    return set_activity_status_flag(entity_id, "currency", True, steward_id)

def deactivate_currency(entity_id, steward_id):
    return set_activity_status_flag(entity_id, "currency", False, steward_id)

def activate_namespace(entity_id, steward_id):
    return set_activity_status_flag(entity_id, "namespace", True, steward_id)

def deactivate_namespace(entity_id, steward_id):
    return set_activity_status_flag(entity_id, "namespace", False, steward_id)

#==============================================================================
#

def set_open_status_flag(entity_id, entity_type, open, steward_id):
    if entity_type == "namespace":
        table = "namespaces"
    elif entity_type == "currency":
        table = "currencies"
    else:
        return "Invalid type specified: must be a namespace or currency"
    if open:
        open_state = 1
    else:
        open_state = 0
    steward_fph, steward_hrns, p_etypes, m = identify_entity(steward_id)
    if not steward_fph:
        return steward_id + " is not a registered identifier"
    if not ("primid" in p_etypes):
        return "Identifier " + steward_id + " has no login identity"
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if not entity_fph:
        return entity_id + " is not a registered identifier"
    if not (entity_type in etypes):
        return "Identifier " + entity_hrns + " has no " + entity_type
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stewards_fph_list FROM " + table + " WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        if result is None: # (should never happen)
            cursor.close()
            return "The entity " + entity_hrns + " has no stewardships"
        stewards_fph_list = pickle.loads(result[0])
        if not (steward_fph in stewards_fph_list):
            cursor.close()
            return steward_hrns + " is not a steward of " + entity_hrns
        cursor.execute(
            "UPDATE " + table + " SET open = ? WHERE entity_fph = ?",
            (open_state, entity_fph)
        )
        conn.commit()
        cursor.close()

    return ""

def open_namespace(entity_id, steward_id):
    return set_open_status_flag(entity_id, "namespace", True, steward_id)

def close_namespace(entity_id, steward_id):
    return set_open_status_flag(entity_id, "namespace", False, steward_id)

def open_currency(entity_id, steward_id):
    return set_open_status_flag(entity_id, "currency", True, steward_id)

def close_currency(entity_id, steward_id):
    return set_open_status_flag(entity_id, "currency", False, steward_id)

#==============================================================================
#
# 2026-06-04:
#
# The steward and stewradship add/remove sections hould be separated because
# the entities may be registered within different clades (and therefore in
# different SQLite files).

# A steward is added to or removed from the entity (*namespace* or *currency*):
#
def add_or_remove_steward(
        entity_id,          # HRNS or FPH identifier
        entity_type,        # namespace | currency
        operation,          # add | remove
        auth_steward_id,    # The steward authorizing the change
        other_steward_id    # The steward affected
    ):
    if entity_type == "namespace":
        table = "namespaces"
        sc = "n"
    elif entity_type == "currency":
        table = "currencies"
        sc = "c"
    else:
        return "Invalid type specified: must be a namespace or currency"
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    # Does the target entity identifer exist?
    if not entity_fph:
        return entity_id + " is not a registered identifier"
    # If so, does it has a *namespace* or *currency* attached to it?
    if not (entity_type in etypes):
        return "Identifier " + entity_hrns + " has no " + entity_type
    # Is the authorizing steward a registered *primid*?:
    auth_steward_fph, auth_steward_hrns, p_etypes, \
    m = identify_entity(auth_steward_id)
    if not auth_steward_fph:
        return auth_steward_id + " is not a registered identifier"
    if not ("primid" in p_etypes):
        return "Identifier " + auth_steward_id + " has no primid"
    # Is the added/removed steward a registered *primid*?:
    other_steward_fph, other_steward_hrns, p_etypes, \
    m = identify_entity(other_steward_id)
    if not other_steward_fph:
        return other_steward_id + " is not a registered identifier"
    if not ("primid" in p_etypes):
        return "Identifier " + other_steward_id + " has no primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stewards_fph_list FROM " + table + " WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        if result is None: # (should never happen)
            cursor.close()
            return "The entity " + entity_hrns + " has no stewards"
        stewards_fph_list = pickle.loads(result[0])
        if not (auth_steward_fph in stewards_fph_list):
            cursor.close()
            return auth_steward_hrns + " is not a steward of " + entity_hrns
        if operation == "add":
            if other_steward_fph in stewards_fph_list:
                cursor.close()
                return other_steward_hrns + " is already a steward of " \
                       + entity_type + " " + entity_hrns
            else:
                stewards_fph_list.append(other_steward_fph)
        elif operation == "remove":
            if not (other_steward_fph in stewards_fph_list):
                cursor.close()
                return other_steward_hrns + " is not a steward of " \
                       + entity_type + " " + entity_hrns
            else:
                stewards_fph_list.remove(other_steward_fph)
        else:
            cursor.close()
            return ""
        cursor.execute(
            "UPDATE " + table + " SET stewards_fph_list = ? " \
            + "WHERE entity_fph = ?",
            (pickle.dumps(stewards_fph_list), entity_fph)
        )
        conn.commit()
        cursor.close()
        return ""
    return ""

# An entity (*namespace* or *currency*) is added to or removed from a *primid*
# stewardships list:'
#
def add_or_remove_stewardship(
        entity_id,          # HRNS or FPH identifier
        entity_type,        # namespace | currency
        operation,          # add | remove
        auth_steward_id,    # The steward authorizing the change
        other_steward_id    # The steward affected
    ):
    if entity_type == "namespace":
        table = "namespaces"
        sc = "n"
    elif entity_type == "currency":
        table = "currencies"
        sc = "c"
    else:
        return "Invalid type specified: must be a namespace or currency"
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    # Does the target entity identifer exist?
    if not entity_fph:
        return entity_id + " is not a registered identifier"
    # If so, does it has a *namespace* or *currency* attached to it?
    if not (entity_type in etypes):
        return "Identifier " + entity_hrns + " has no " + entity_type
    # Is the authorizing steward a registered *primid*?:
    auth_steward_fph, auth_steward_hrns, p_etypes, \
    m = identify_entity(auth_steward_id)
    if not auth_steward_fph:
        return auth_steward_id + " is not a registered identifier"
    if not ("primid" in p_etypes):
        return "Identifier " + auth_steward_id + " has no primid"
    # Is the added/removed steward a registered *primid*?:
    other_steward_fph, other_steward_hrns, p_etypes, \
    m = identify_entity(other_steward_id)
    if not other_steward_fph:
        return other_steward_id + " is not a registered identifier"
    if not ("primid" in p_etypes):
        return "Identifier " + other_steward_id + " has no primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT " + sc + "stewardships_fph_list FROM primids " \
            + "WHERE entity_fph = ?",
            (other_steward_fph,)
        )
        result = cursor.fetchone()
        if result is None: # (should never happen)
            cursor.close()
            return "The primid " + other_steward_hrns + " has no stewardships"
        stewardships_fph_list = pickle.loads(result[0])
        if not (entity_fph in stewardships_fph_list):
            cursor.close()
            return entity_hrns + " is not stewarded by " + other_steward_hrns
        if operation == "add":
            if entity_fph in stewardships_fph_list:
                cursor.close()
                return entity_hrns + " already has " + other_steward_hrns \
                                   + " among its stewards"
            else:
                stewardships_fph_list.append(entity_fph)
        elif operation == "remove":
            if not (entity_fph in stewardships_fph_list):
                cursor.close()
                return entity_hrns + " is not among the stewardships of " \
                       + other_steward_hrns
            else:
                stewardships_fph_list.remove(entity_fph)
        else:
            cursor.close()
            return ""
        cursor.execute(
            "UPDATE primids SET " + sc + "stewardships_fph_list = ? " \
            + "WHERE entity_fph = ?",
            (pickle.dumps(stewardships_fph_list), other_steward_fph)
        )
        conn.commit()
        cursor.close()
        return ""
    return ""

def add_namespace_steward(entity_id, auth_steward_id, new_steward_id):
    m = add_or_remove_steward(
            entity_id, "namespace", "add", auth_steward_id, new_steward_id
        )
    n = add_or_remove_stewardship(
            entity_id, "namespace", "add", auth_steward_id, new_steward_id
        )
    return m + n

def remove_namespace_steward(entity_id, auth_steward_id, other_steward_id):
    m = add_or_remove_steward(
            entity_id, "namespace", "remove", auth_steward_id, other_steward_id
        )
    n = add_or_remove_stewardship(
            entity_id, "namespace", "remove", auth_steward_id, other_steward_id
        )
    return m + n

def add_currency_steward(entity_id, auth_steward_id, new_steward_id):
    m = add_or_remove_steward(
            entity_id, "currency", "add", auth_steward_id, new_steward_id
        )
    n = add_or_remove_stewardship(
            entity_id, "currency", "add", auth_steward_id, new_steward_id
        )
    return m + n

def remove_currency_steward(entity_id, auth_steward_id, other_steward_id):
    m = add_or_remove_steward(
            entity_id, "currency", "remove", auth_steward_id, other_steward_id
        )
    n = add_or_remove_stewardship(
            entity_id, "currency", "remove", auth_steward_id, other_steward_id
        )
    return m + n

#------------------------------------------------------------------------------

def set_currency_parameter(currency_id, parameter, ctype, steward_id):

    currency_fph, currency_hrns, \
    active, open, private, sandbox, \
    currency_type, currency_category, currency_units, \
    currency_metrical_equivalence, currency_dimensions, \
    prefix, suffix, default_account_name, \
    stewards_list, m = get_currency_properties(currency_id)
    if not currency_fph:
        return currency_id + " is not a registered identifier"

    steward_fph, steward_hrns, etypes, m = identify_entity(steward_id)
    if not steward_fph:
        return steward_id + " is not a registered identifier"
    if not ("primid" in etypes):
        return steward_hrns + " is not a registered primid"
    if not (steward_fph in stewards_list):
        return steward_hrns + " is not a steward of " + currency_hrns

    if parameter == "type":
        if ctype in [
                        "scalar", "vector", "matrix",
                        "tuple", "mapping", "pointer",
                        "time_series", "trigger_threshold"
                    ]:
            if ctype == currency_type: # nothing to change
                return ""
            else:
                with sqlite3.connect(ENTITIES_DB) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE currencies SET type = ? WHERE entity_fph = ?",
                        (ctype, currency_fph)
                    )
                    conn.commit()
                    cursor.close()
        else:
            return(ctype + " is invalid for " + parameter)
    elif parameter == "category":
        if ctype in ["money", "count", "vote", "measure"]:
            if ctype == currency_category: # nothing to change
                return ""
            else:
                with sqlite3.connect(ENTITIES_DB) as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE currencies SET category = ? " \
                        + "WHERE entity_fph = ?",
                        (ctype, currency_fph)
                    )
                    conn.commit()
                    cursor.close()
    elif parameter == "units":
        return ""
    elif parameter == "metrical_equivalence":
        return ""
    elif parameter == "dimensions":
        return ""
    else:
        return ""
    return ""



# List the clades within the ancestry of an identifier
def list_ancestors_fph(entity_id):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if not entity_fph:
        return [], [], "Invalid identifier"
    ancestors = []  # list of ancestors
    clades = []     # list of clades (PNSR) within those ancestors
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
        cursor = conn.cursor()
        digging_through_ancestry = True
        while digging_through_ancestry:
            cursor.execute(
                "SELECT parent_fph, pnsr_fph FROM entities_registered " \
                + "WHERE entity_fph = ?",
                (entity_fph,)
            )
            result = cursor.fetchone()
            if (result is None) \
            or (result[0] is None) \
            or (result[0] == SUBSTRATE_FPH): # no more ancestors
                break
            else:
                parent_fph = result[0]  # the parent FPH
                ancestors.append(parent_fph)
                entity_fph = parent_fph # ready to dig another level
                pnsr_fph = result[1]    # the PNSR (clade) FPH
                if not (pnsr_fph in clades):
                    clades.append(pnsr_fph)
        digging_through_ancestry = False
        cursor.close()
    return ancestors, clades, ""

def most_recent_clade(entity_id):
    ancestors, clades, m = list_ancestors_fph(entity_id)
    if m:
        return "", m
    if len(clades) > 0:
        return clades[0], ""
    else:
        return "", ""

def most_distant_clade(entity_id):
    ancestors, clades, m = list_ancestors_fph(entity_id)
    if m:
        return "", m
    if len(clades) > 0:
        return clades[-1], ""
    else:
        return "", ""

def most_recent_concestor(entity1_id, entity2_id):
    entity1_fph, entity1_hrns, etypes, m = identify_entity(entity1_id)
    if m:
        return "", "", "", m
    entity2_fph, entity2_hrns, etypes, m = identify_entity(entity2_id)
    if m:
        return "", "", "", m
    ancestors1 = entity1_hrns.split(NSS)
    ancestors2 = entity2_hrns.split(NSS)
    depth = min(len(ancestors1), len(ancestors2))
    concestor = []
    while (ancestors1[-1] == ancestors2[-1]) and (depth > 1):
        n1 = ancestors1.pop()
        n2 = ancestors2.pop()
        concestor.append(n1)
        depth -= 1
    concestor.reverse()
    # The abbreviated HRNS returned are the residue of the ancestral chains
    # following removal of their concestor:
    return NSS.join(ancestors1), NSS.join(ancestors2), NSS.join(concestor), ""


def get_list_concestor(hrns_list):
    splits_list = []
    for hrns in hrns_list:
        splits_list.append(hrns.split(NSS))
    # Find length of shortest HRNS in order to ensure that no attempt is made to
    # operate on an empty list:
    l = []
    for i in range(len(splits_list)):
        l.append(len(splits_list[i]))
    l_min = min(l)
    depth = l_min - 1
    if l_min == 1: # the most recent concestor is the SUBSTRATE (a valid result)
        return "" # HRNS of SUBSTRATE
    concestor = []
    while depth:
        depth -= 1
        # Compare the most distant ancestors
        c = splits_list[0][-1]
        for h in range(len(splits_list)): # each HRNS split-list
            if splits_list[h][-1] != c:
                break
        # At each iteration, the most distant ancestor common to all HRNS lists
        # is appended to the concestor and removed from all the HRNS lists.
        concestor.append(c)
        for h in range(len(splits_list)): # each HRNS split-list
            splits_list[h].pop()
    concestor.reverse()
    return NSS.join(concestor)


def prune_payment_pair_hrns(currency_id, payer_ahid_id):
    currency_hrns_short, payer_ahid_hrns_short, concestor_hrns, \
    m = most_recent_concestor(currency_id, payer_ahid_id)
    return currency_hrns_short, payer_ahid_hrns_short, concestor_hrns, m

# Display an HRNS with the specified concestor removed:
def _hrns_strip_concestor(entity_id, concestor_id):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if not entity_fph:
        return "", "invalid entity_id" # invalid entity_id
    concestor_fph, concestor_hrns, etypes, m = identify_entity(concestor_id)
    if not concestor_fph:
        return "", "invalid concestor_id"
    return entity_hrns.replace(concestor_hrns, "").strip(NSS), ""

def hrns_strip_concestor(entity_hrns, concestor_hrns):
    entity_hrns_l = entity_hrns.split(NSS)
    concestor_hrns_l = concestor_hrns.split(NSS)
    for i in range(len(concestor_hrns_l)):
        entity_hrns_l.pop()
    return NSS.join(entity_hrns_l), ""

# If and only if the identifier lies within a private *namespace* tree (clade),
# the clade HRNS is removed from the identifier HRNS to abbreviate the display.
def display_hrns_local(entity_id):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if not entity_fph:
        return "", "", "invalid entity_id" # invalid entity_id
    clade_fph, m = most_recent_clade(entity_id)
    if clade_fph == entity_fph:
        return entity_hrns, entity_hrns, ""
    clade_hrns = fph_to_hrns(clade_fph)
    return entity_hrns.replace(clade_hrns, "").strip(NSS), clade_hrns, ""
