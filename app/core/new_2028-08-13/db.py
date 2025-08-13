import sqlite3
#import random
#import os
#import pickle
#from pathlib import Path
#from string import ascii_lowercase

from app.core.constants import ENTITIES_DB
from app.core.constants import PAYMENTS_DB
from app.core.constants import DB_DIR
from app.core.constants import DB_BKP_DIR
#from app.core.constants import HUBS_DB
#from app.core.constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
#from app.core.constants import SUBSTRATE_FPH
#from app.core.constants import VERSION, CONFIG
from app.core.constants import NSS # NamseSpace Separator character

#from app.core.common import filename_timestamp as timestamp
#from app.core.common import ledger_timestamp
#from app.core.common import nshash
#from app.core.common import unixtime_str

#from app.core.messaging import send_message

#from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
#from app.core.fph_hrns_maps import delete_fph_from_map

#from app.core.dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
#from app.core.dbm_functions import dbm_create_map

#from app.core.auth import auth_hash, check_auth_hash, generate_access_token

#from app.core.regexp_list import *

#from app.core.unix_functions import fcopy

#from app.core.cctld_list import *


#from app.core.regexp_list import re_pvalue
#from app.core.regexp_list import re_pairaccountname

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
            + "accounts_fph_list BLOB, " \
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
            + "category TEXT DEFAULT ''" \
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
