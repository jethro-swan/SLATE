import sqlite3
import random
import os
import pickle
from pathlib import Path
from string import ascii_lowercase

from .constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
from .constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from .constants import UNIVERSAL_ROOT_FPH
from .common import filename_timestamp as timestamp
from .common import nshash
from .fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from .dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from .dbm_functions import dbm_create_map
from .auth import auth_hash, generate_access_token
from .regexp_list import *
from .unix_functions import fcopy
from .cctld_list import *

# NB  This version was working at 2024-10-15 before
#     (a) the common entity properties were moved to a separate table;
#     (b) a distinction was introduced between *primid* and *secid*; and
#     (c) new functions were added to accommodate the changes above.



debugging = True
#max_hrns_depth = 0

#------------------------------------------------------------------------------
# In NESTS the FPH has so far been formed as the hash of the FIP, but making it
# the hash of the HRNS instead will simplify compatibility between SLATE and
# NESTS and speed up the HRNS to FPH mapping without having any signifcant
# impact on the FPH to HRNS and FPH to FIP mappings.

#==============================================================================
# Create the SQLite entities database:

def create_entities_db():

    if os.path.exists(ENTITIES_DB):
        # If the database exists already, it is deleted after a time-stamped
        # copy has been saved.
        fcopy(ENTITIES_DB, DB_BKP_DIR + '/entities_' + timestamp() + '.db')
        os.remove(ENTITIES_DB)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # A table is created for the entities common properties:
        cursor.execute(
            """
    	    CREATE TABLE IF NOT EXISTS entity_properties (
                entity_fph TEXT PRIMARY KEY,
                parent_namespace_fph TEXT,
                entity_type TEXT,
                active INTEGER NOT NULL
            );
            """
        )
        # Create agents table:
        cursor.execute(
            """
    	    CREATE TABLE IF NOT EXISTS agents (
                entity_fph TEXT PRIMARY KEY,
                parent_namespace_fph TEXT,
                entity_type TEXT,
                agent_realname TEXT,
                agent_email_1 TEXT NOT NULL,
                accounts_fph_list BLOB,
                stewardships_fph_list BLOB,
                password_hash TEXT NOT NULL,
                pin TEXT,
                access_token_hash TEXT,
                active INTEGER NOT NULL
            );
            """
        )
        # Create currencies table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS currencies (
                entity_fph TEXT PRIMARY KEY,
                parent_namespace_fph TEXT,
                entity_type TEXT,
                currency_prefix TEXT,
                currency_suffix TEXT,
                accounts_fph_list BLOB,
                stewards_fph_list BLOB,
                active INTEGER NOT NULL
            );
            """
        )
        # Create accounts table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS accounts (
                entity_fph TEXT PRIMARY KEY,
                parent_namespace_fph TEXT,
                entity_type TEXT,
                account_owner_fph TEXT NOT NULL,
                account_currency_fph TEXT NOT NULL,
                account_balance INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL
            );
            """
        )
        # Create namespaces table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS namespaces (
                entity_fph TEXT PRIMARY KEY,
                parent_namespace_fph TEXT,
                entity_type TEXT,
                stewards_fph_list TEXT NOT NULL,
                active INTEGER NOT NULL
            );
            """
        )
        # Create stewards table (for namespaces and currencies):
#        cursor.execute(
#            """
#            CREATE TABLE IF NOT EXISTS stewards (
#                entity_fph TEXT,
#                primid_fph TEXT
#            );
#            """
#        )
        # Create stewardships table (for namespaces and currencies):
#        cursor.execute(
#            """
#            CREATE TABLE IF NOT EXISTS stewardships (
#                primid_fph TEXT,
#                entity_fph TEXT
#            );
#            """
#        )
        # Create currency_accounts table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS currency_accounts (
                currency_fph TEXT,
                account_fph TEXT
            );
            """
        )
        # Create agent_accounts table (agent = primid or secid):
#        cursor.execute(
#            """
#            CREATE TABLE IF NOT EXISTS agent_accounts (
#                agent_fph TEXT,
#                account_fph TEXT
#            );
#            """
#        )
        # Create secids table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS secids (
                secid_fph TEXT,
                primid_fph TEXT
            );
            """
        )
        # Create login table:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS login (
                primid_fph TEXT,
                login_id_fph TEXT,
                login_authenticated INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        conn.commit()
        cursor.close()

#==============================================================================
# The initial (minimal) set of entities created in a SLATE node are constrained
# by dependency rules similar to those in NESTS although slightly simpler
# because
# (a) there is only one class of agent (equivalent to primary identity);
# (b) there is only one namespace separator (".");
# (c) only the Latin alphabet is used; and
# (b) there is only one class of currency (money).
# (see https://nests.lrc.org.uk/entity_dependencies.html
#
# Every SLATE or NESTS installation must be provided with a minimal set of
# pre-existing entities:
#
# - A namespace to be the parent both of the initial agent and the initial
#   currencies. For simplicity, this is given the name "global".
#
#   An agent (primary identity) to serve as the initial steward of the first
#   namespace or currency created after installation.
#
#   This agent is also the initial steward of all of the the geographical root
#   namespaces create during installation. It belongs (at least initially) to
#   the system adminstrator who creates the NESTS hub.
#
#   The default name (HRNS) of this agent is "gaia.global".
#
# - A currency (global in scope) which can be can be used to create the initial
#   accounts for the first new agents created. The default name (HRNS) of this
#   currency is "hours.global" and its default initial steward's HRNS for this
#   is "gaia.global".
#
# - When the initial agent "gaia.global" is created, an account with HRNS
#   "hours.gaia.global" is created for it in the currency "hours.global" (the
#   default currency for identities created within the "global" namespace).

def create_seed_entities():

    # A note on namespaces:
    #
    # The name of every entity, of whatever type, is contained within a
    # namespace.
    #
    # Namespaces fall into two categories:
    # (1) The term *namespace* is generally used to mean a non-terminal
    #     namespace that can contain the name of any type of entity.
    # (2) The name of an *agent* identifies a special type of namespace (a
    #     "terminal namespace") that can contain only the names of *accounts*.
    #     Despite this property, they are generally referred to only as
    #     *agents*.
    # (3) A *root namespace* is one the name of which is not contained within
    #     a named namespace. Such *root namespace* all share an unnamed
    #     namespace ("") which contains only the names of *root namespaces*,
    #     which include (typically) geographical containers (such as "uk",
    #     "ca", "es", "de", "fr", etc.) or containers having a different
    #     significance.
    #     The first *root namespace* created (the "seed namespace") is named
    #     "global".
    # (4) The properties of *agents* (as terminal namespace) differ slightly
    #     between NESTS and SLATE:
    #     In NESTS:
    #     - The name of an *account* can be contained within a namespace of any
    #       type.
    #     - The name of that *account* can comprise any string.
    #     - The *account* may be in any *currency".
    #     In SLATE:
    #     - The name of an *account* can be contained within an *agent*
    #       (serving as a terminal namespace), the owner of the *account*.
    #     - The name of an *account* is the same as the name of its *currency*.

    # Seed entities (see https://nests.lrc.org.uk/entity_dependencies.html)
    # by HRNS:
    root_hrns = ""          # The nameless namespace from which all others
                            # ramify.
    seed_namespace_hrns     = "global"
                            # parent namespace:     ""
                            # initial steward:      "gaia.global"

    seed_currency_hrns      = "hours.global"
    seed_currency_parent_ns = "global"
                            # initial steward:      "gaia.global"

    seed_agent_hrns         = "gaia.global"
    seed_agent_parent_ns    = "global"
                            # initial account:      "hours.gaia.global"
                            # stewardships:         "global" (namespace)
                            #                       "hours.global" (currency)

    seed_account_hrns       = "hours.gaia.global"
    seed_account_parent_ns  = "gaia.global"
                            # owned by:             "gaia.global"
                            # in currency:          "hours.global"

    # Seed entities by FPH:
    root_fph = nshash("")   # The nameless namespace from which all others
                            # ramify. This has already been added to the
                            # FPH>HRNS map (at the point of its creation).
                            #
                            # The seed entities are now mapped to their FPH and
                            # added to the FPH>HRNS map:
    seed_namespace_fph, m   = hrns_to_fph(seed_namespace_hrns)
    seed_currency_fph, m    = hrns_to_fph(seed_currency_hrns)
    seed_agent_fph, m       = hrns_to_fph(seed_agent_hrns)
    seed_acct_fph, m        = hrns_to_fph(seed_account_hrns)

    # Every *namespace* or *currency* needs a set of stewards. At this point
    # only one *agent* ("gaia.global") exists so, for the time being, this
    # must serve as the sole steward for the "global" *namespace* and the
    # "hours.global" *currency*.
    stewards_fph_list       = [seed_agent_fph]
    stewards_fph_blob       = pickle.dumps(stewards_fph_list)
    #
    # The these stewardships must be added to the seed *agent* ("gaia.global"):
    stewardships_fph_list   = [seed_namespace_hrns, seed_currency_hrns]
    stewardships_fph_blob   = pickle.dumps(stewardships_fph_list)
    #
    # (These FPH lists are saved in SQLite as blobs, for which reason they must
    # be serialized.)

    # The seed *account* ("hours.gaia.global") is in the seed *currency*
    # ("hours.global"):
    account_currency_fph    = seed_currency_fph
    # An *account* can obviously have only one *currency*, so this does not
    # have to be saved as a serialized list.
    #
    # At this point, the seed *currency* ("hours.global") has only one
    # *account* ("hours.gaia.global"):
    currency_accts_fph_list = [seed_acct_fph]
    currency_accts_fph_blob = pickle.dumps(currency_accts_fph_list)

    # (In due course, the default values for the follwing will be read from a
    # configuration file.)
    sa_realname             = "Gaia"
    sa_email                = "gaia@lrc.org.uk"
    sa_password             = "Gl0balM3ltd0wn"
    sa_password_hash        = auth_hash(sa_password)
    sa_pin                  = "123456"
    sa_access_token         = "1a1b2c3d5e8f13g21f34e55d89e144ff"
    sa_access_token_hash    = auth_hash(sa_access_token)
    # Seed agent's initial account:
    #seed_agent_acct_hrns = "hours.gaia.global"
    #seed_agent_accts_fph, m = hrns_to_fph(seed_agent_acct_hrns)
    sa_accts_fph_list       = [seed_acct_fph]
    sa_accts_fph_blob       = pickle.dumps(sa_accts_fph_list)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO agents (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                agent_realname,
                agent_email_1,
                accounts_fph_list,
                stewardships_fph_list,
                password_hash,
                pin,
                access_token_hash,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                seed_agent_fph,
                nshash(seed_agent_parent_ns),
                "agent",
                sa_realname,
                sa_email,
                sa_accts_fph_blob,
                stewardships_fph_blob,
                sa_password_hash,
                sa_pin,
                sa_access_token_hash,
                True
            )
        )

        cursor.execute(
            """
            INSERT INTO currencies (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                currency_prefix,
                currency_suffix,
                accounts_fph_list,
                stewards_fph_list,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                seed_currency_fph,
                nshash(seed_currency_parent_ns),
                "currency",
                "",
                "h",
                currency_accts_fph_blob,
                stewards_fph_blob,
                True
            )
        )

        cursor.execute(
            """
            INSERT INTO namespaces (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                stewards_fph_list,
                active
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                seed_namespace_fph,
                root_fph,
                "namespace",
                stewards_fph_blob,
                True
            )
        )

        # NB The namespace "global" is a special case in that it has no parent
        #    namespace.

        cursor.execute(
            """
            INSERT INTO accounts (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                account_owner_fph,
                account_currency_fph,
                account_balance,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                seed_acct_fph,
                nshash(seed_account_parent_ns),
                "account",
                seed_agent_fph,
                seed_currency_fph,
                0,
                True
            )
        )

        conn.commit()
        cursor.close()





#==============================================================================
#def get_currency_hrns(currency_fph):
#    return fph_to_hrns(currency_fph)


#==============================================================================
def get_currency_name(currency_fph):
    hrns = fph_to_hrns(currency_fph)
    if hrns == "":
        return ""
    else:
        hrnsa = hrns.split(".")
        return hrnsa[0]

#==============================================================================
# A new account is created in a specified currency:

def new_account(
        agent_fph,
        currency_fph
    ):
    # In contrast to NESTS, every account sits under the agent that owns it,
    # e.g.  hours.crun.finchley.london.uk
    # so a parent namespace does not have to be specified separately.

    if not re_fph.match(agent_fph):
        return "", "", "Invalid agent FPH: " + agent_fph

    if not re_fph.match(currency_fph):
        return "", "", "Invalid currency FPH: " + currency_fph

    agent_hrns = fph_to_hrns(agent_fph)
    currency_name = get_currency_name(currency_fph)
    account_hrns = currency_name + "." + agent_hrns

    if fph_to_hrns(nshash(account_hrns)):
        #print("\t" + account_hrns + " exists already")
        return "", "", "collision: " + account_hrns

    account_fph, m = hrns_to_fph(account_hrns)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO accounts (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                account_owner_fph,
                account_currency_fph,
                account_balance,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_fph,
                agent_fph,      # In the case of an *account*, the owner's
                "account",      # private *namespace* is always the parent.
                agent_fph,
                currency_fph,
                0,
                True
            )
        )
        cursor.execute(
            """
            SELECT accounts_fph_list FROM agents WHERE entity_fph = ?
            """,
            (agent_fph,)
        )
        accounts_fph_blob = cursor.fetchone()
        if accounts_fph_blob is not None:
            accounts_fph_list = pickle.loads(accounts_fph_blob[0])
            accounts_fph_list.append(account_fph)
            accounts_fph_blob = pickle.dumps(accounts_fph_list)
            cursor.execute(
                """
                UPDATE agents SET accounts_fph_list = ?
                WHERE entity_fph = ?
                """,
                (accounts_fph_blob, agent_fph)
            )

        cursor.execute(
            """
            INSERT INTO currency_accounts (currency_fph, account_fph)
            VALUES (?, ?)
            """,
            (currency_fph, account_fph)
        )

        conn.commit()
        cursor.close()

    if m:
        return "", "", m
    else:
        return account_fph, account_hrns, ""

#==============================================================================
# A new agent is created in the specified namespace.
# An account is created for that agent in the currency specified.

def new_agent(
        username,
        parent_namespace_fph,
        realname,
        email_address,
        password,
        pin,
        initial_currency_fph,
        initial_stewardship_fph
    ):

    if not re_fph.match(parent_namespace_fph):
        return "", "", "", "Invalid parent namespace: " + parent_namespace_fph

    if not re_fph.match(initial_currency_fph):
        return "", "", "", "Invalid currency: " + initial_currency_fph

    namespace_hrns = fph_to_hrns(parent_namespace_fph)
    agent_hrns = username + "." + namespace_hrns

    if fph_to_hrns(nshash(agent_hrns)):
        return "", "", "", "collision:  " + agent_hrns

    agent_fph, m = hrns_to_fph(agent_hrns)

    if not re_email.match(email_address):
        return("Invalid email address. Agent not created.")

    password_hash = auth_hash(password)

    account_fph, account_hrns, m = new_account(agent_fph, initial_currency_fph)

    accounts_fph_list = pickle.dumps([account_fph])
    stewardships_fph_list = pickle.dumps([])

    access_token = generate_access_token()
    access_token_hash = auth_hash(access_token)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO agents (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                agent_realname,
                agent_email_1,
                accounts_fph_list,
                stewardships_fph_list,
                password_hash,
                pin,
                access_token_hash,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                agent_fph,
                parent_namespace_fph,
                "agent",
                realname,
                email_address,
                accounts_fph_list,
                stewardships_fph_list,
                password_hash,
                pin,
                access_token_hash,
                True
            )
        )
        conn.commit()
        cursor.close()

    return agent_fph, agent_hrns, access_token, ""

# Although the initial access token is generated automatically here, it may be
# updated by the agent at any time.

#==============================================================================
# A new namespace is created:

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
        return "", "", "collision:  " + namespace_hrns

    namespace_fph, m = hrns_to_fph(namespace_hrns)

    stewards_fph_blob = pickle.dumps(list([initial_steward_fph]))

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO namespaces (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                stewards_fph_list,
                active
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                namespace_fph,
                parent_namespace_fph,
                "namespace",
                stewards_fph_blob,
                True
            )
        )
        conn.commit()
        cursor.close()

    return namespace_fph, namespace_hrns, ""

#==============================================================================
# A new currency is added:

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
        return "", "", "collision:  " + currency_hrns

    currency_fph, m = hrns_to_fph(currency_hrns)

    initial_steward_hrns = fph_to_hrns(initial_steward_fph)
    initial_account_hrns = currency_name + "." + initial_steward_hrns
    initial_account_fph, m = hrns_to_fph(initial_account_hrns)
    accounts_fph_list = pickle.dumps([initial_account_fph])

    stewards_fph_list = pickle.dumps([initial_steward_fph])

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO currencies (
                entity_fph,
                parent_namespace_fph,
                entity_type,
                currency_prefix,
                currency_suffix,
                accounts_fph_list,
                stewards_fph_list,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                currency_fph,
                parent_namespace_fph,
                "currency",
                currency_prefix,
                currency_suffix,
                accounts_fph_list,
                stewards_fph_list,
                True
            )
        )
        conn.commit()
        cursor.close()

    return currency_fph, currency_hrns, ""

#==============================================================================

def set_web_password_hash(agent_fph, password):

    return ""



def agent_update_realname(agent_fph, new_name):

    return ""

#------------------------------------------------------------------------------
def agent_update_email(agent_fph, new_email):

    return ""

#------------------------------------------------------------------------------
def agent_update_login(agent_fph, new_password, new_pin):

    return new_access_token, ""


#==============================================================================
# A set of "pseudo-TLD" root namespaces, each having the same null parent
# nameaspace ("": root_fph) and the same initial steward ("gaia.global":
# seed_agent_fph):

def create_quasitld_set(full = False, display = False):

    if full:
        cctld_list_here = cctld_list
    else:
        cctld_list_here = cctld_reduced_list

    # This is a crude progress counter to indicate the sequence in which random
    # entities are created or an HRNS collision detected.
    progress_count = 80

    root_fph = nshash("")
    seed_agent_fph = nshash("gaia.global")
    for tld in cctld_list_here:
        namespace_fph, namespace_hrns, m = new_namespace(
                                               tld,
                                               root_fph,
                                               seed_agent_fph
                                           )
        if debugging:
            message = ""
            if m:
                message = " | " + m
            if display:
                print(namespace_fph + " > " + namespace_hrns + message)
            else:
                sys.stdout.write(".")
                sys.stdout.flush()
                progress_count -= 1
                if progress_count == 0:
                    progress_count = 80
                    sys.stdout.write("\n")
                    sys.stdout.flush()

    if display:
        print("\n" + "="*160 + "\n")


#==============================================================================
# List the agent's accounts: KEEP
def list_agent_accounts(agent_fph):
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT accounts_fph_list FROM agents WHERE entity_fph = ?",
            (agent_fph,)
        )
        agent_properties = cursor.fetchone()
        cursor.close()
        if agent_properties is not None:
            accounts_fph_blob = agent_properties[0]
            if accounts_fph_blob is not None:
                accounts_fph_list = pickle.loads(accounts_fph_blob)
                return accounts_fph_list, ""    # list + message
            else:
                return [], "Accounts FPH list invalid"
        else:
            return [], "Agent properties list invalid"


#==============================================================================
# Get the currency of an account: KEEP
def get_account_currency(account_fph):
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_currency_fph FROM accounts WHERE entity_fph = ?",
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

def list_currency_accounts(currency_fph):

    if not re_fph.match(currency_fph):
        return [], "Invalid FPH"
    if not get_entity_type(currency_fph) == "currency":
        return [], "FPH " + currency_fph + " is not a currency"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_fph FROM currency_accounts WHERE entity_fph = ?",
            (currency_fph,)
        )
        accounts_fph_list = cursor.fetchall()
        cursor.close()

    return accounts_fph_list, ""    # list + message

#==============================================================================
# Identify the account (if any) in which the agent has access to the specified
# currency: KEEP

def list_agent_currency_accounts(agent_fph, currency_fph):

    accounts_fph_list = []
    for account_fph in acct_fph_list:
        if get_account_currency(account_fph) == currency_fph:
            accounts_fph_list.append(currency_fph)
    return accounts_fph_list






#==============================================================================
# List the agent's accounts' currencies: KEEP
def list_agent_currencies(agent_fph): # in which an agent has accounts
    accounts_fph_list, m = list_agent_accounts(agent_fph)
    currencies_fph_list = []
    for account_fph in accounts_fph_list:
        currencies_fph_list.append(get_account_currency(account_fph))
    return currencies_fph_list    # list

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
# Get the entity type:
def get_entity_type(entity_fph):

    if not re_fph.match(entity_fph):
        return "", "Invalid FPH: " + entity_fph

    # A table name cannot be passed using ?-substitution. Therefore .format( )
    # must be used. See
    # https://stackoverflow.com/questions/3247183/variable-table-name-in-sqlite

    entity_fph = "'" + entity_fph + "'" # wrapped to enable SQLite to accept it.

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        # Using table names: "namespaces", "currencys", "agents" and "accounts"
        for entity_table in ["namespaces", "currencies", "agents", "accounts"]:
            cursor.execute(
                """
                SELECT entity_type FROM {} WHERE entity_fph = {}
                """.format(entity_table,entity_fph)
            )
            result = cursor.fetchone()
            if result is not None:
                entity_type = result[0] # entity_type
                if entity_type:
                    cursor.close()
                    return entity_type, ""
        cursor.close()

    return "", "Entity type unidentifiable"

#==============================================================================

def account_status(account_fph): # returns: exists (boolean), active (boolean),
                                 # currency (FPH), owner (FPH), error message
    if not re_fph.match(account_fph):
        return False, False, "", "", 0, "Invalid FPH: " + account_fph

    account_fph = "'" + account_fph + "'" # wrapped to enable SQLite to accept it.

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT entity_type, account_owner_fph, account_currency_fph,
                   account_balance, active
            FROM accounts WHERE entity_fph = ?
            """,
            (account_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
    if result is not None:
        entity_type = result[0]
        owner_fph = result[1]
        currency_fph = result[2]
        balance = result[3]
        active = result[4]
    else: # no record for account_fph
        return False, False, "", "", 0, "Account not found"

    if not re_fph.match(owner_fph):
        return False, False, "", "", 0, "Invalid owner FPH: " + owner_fph

    if not re_fph.match(currency_fph):
        return False, False, "", "", 0, "Invalid currency FPH: " + currency_fph

    if not entity_type == "account":
        return False, False, "", "", 0, account_fph + " is not an account"

    if not active:
        return True, False, currency_fph, owner_fph, balance, \
               "Account " + account_fph + " inactive"
    else:
        return True, True, currency_fph, owner_fph, balance, ""






#==============================================================================
# List all currencies named within the specified namespace:

def list_currencies_in_namespace(namespace_fph = ""):

    return currency_fph_list # list


#==============================================================================
# List all agents named within the specified namespace:
def list_agents_in_namespace(namespace_fph = ""):

    return agent_fph_list # list


#==============================================================================
# List all currencies named within the specified namespace:

def list_accounts_in_namespace(namespace_fph = ""):

    return currency_fph_list # list


#==============================================================================
# List all agents named within the specified namespace:
def list_namespaces_in_namespace(namespace_fph = ""):

    return agent_fph_list # list


#==============================================================================
# List all agents named within the specified namespace:
def list_namespaces_below_namespace(namespace_fph = ""):

    return agent_fph_list # list


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
# List the FPH of the currencies in which two agents both have an account:
def list_currencies_in_common_by_fph(a1_fph, a2_fph):
    return list(set(list_currencies(a1_fph)) & set(list_currencies(a2_fph)))

# List the HRNS of the currencies in which two agents both have an account:
def list_currencies_in_common_by_hrns(a1_fph, a2_fph):
    for currency_fph in list_currencies_in_common_by_fph(a1_fph, a2_fph):
        print(fph_to_hrns(currency_fph))

#==============================================================================
# Entities may be identified either by HRNS or by FPH. Given that these are
# very different in structure, they may be identified automatically:

def identify_entity(entity_identifier): # HRNS or FPH
    if re_fph.match(entity_identifier): # this is an FPH
        entity_fph = entity_identifier
        entity_hrns = fph_to_hrns(entity_fph)
        if entity_hrns: # entity exists
            entity_type = get_entity_type(entity_fph)
            return entity_fph, entity_hrns, entity_type, ""
        else:
            return "", "", "", "Entity " + entity_fph + " does not exist"
    elif re_hrns.match(entity_identifier): # this is an HRNS
        entity_hrns = entity_identifier
        entity_fph, m = hrns_to_fph(entity_identifier)
        if entity_fph: # entity exists
            entity_type = get_entity_type(entity_fph)
            return entity_fph, entity_hrns, entity_type, ""
        else:
            return "", "", "", "Entity " + entity_hrns + " does not exist"
    else: # this is not an entity
        return "", "", "", entity_hrns + " is not an entity"

#==============================================================================



#------------------------------------------------------------------------------
# Add steward to namespace or currency:

def add_steward(entity_fph, agent_fph):

    if not re_fph.match(entity_fph):
        return entity_fph + " is not an FPH"
    if not re_fph.match(agent_fph):
        return agent_fph + " is not an FPH"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        etype = get_entity_type(entity_fph)
        if etype == "namespace":
            table = "namespaces"
        elif etype == "currency":
            table = "currencies"
        else:
            return "Invalid entity type"

        select_str = "SELECT stewards_fph_list FROM " + table \
                   + " WHERE entity_fph = ?"
        cursor.execute(select_str, (entity_fph,))
        stewards_fph_blob = cursor.fetchone()[0]
        stewards_fph_list = pickle.loads(stewards_fph_blob)
        stewards_fph_list.append(agent_fph)
        stewards_fph_blob = pickle.dumps(stewards_fph_list)
        update_str = "UPDATE " + table \
                   + " SET stewards_fph_list = ? WHERE entity_fph = ?"
        cursor.execute(update_str, stewards_fph_list)

        select_str = "SELECT stewardships_fph_list FROM agents " \
                   + " WHERE entity_fph = ?"
        cursor.execute(select_str, (entity_fph,))
        stewardships_fph_blob = cursor.fetchone()[0]
        stewardships_fph_list = pickle.loads(stewardships_fph_blob)
        stewardships_fph_list.append(agent_fph)
        stewardships_fph_blob = pickle.dumps(stewardships_fph_list)
        update_str = "UPDATE agents SET stewardships_fph_list = ? " \
                   + "WHERE entity_fph = ?"
        cursor.execute(update_str, stewardships_fph_list)

        conn.commit()
        cursor.close()

    return ""

#------------------------------------------------------------------------------
# An entity may have several stewards and an agent (primid) may have several
# stewardships, so both must be specified to ensure that only the correct pair
# is deleted.
def remove_steward(entity_fph, agent_fph):

    if not re_fph.match(entity_fph):
        return entity_fph + " is not an FPH"
    if not re_fph.match(agent_fph):
        return agent_fph + " is not an FPH"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        etype = get_entity_type(entity_fph)
        if etype == "namespace":
            table = "namespaces"
        elif etype == "currency":
            table = "currencies"
        else:
            return "Invalid entity type"

        select_str = "SELECT stewards_fph_list FROM " + table \
                   + " WHERE entity_fph = ?"
        cursor.execute(select_str, (entity_fph,))
        stewards_fph_blob = cursor.fetchone()[0]
        stewards_fph_list = pickle.loads(stewards_fph_blob)
        stewards_fph_list.remove(agent_fph)
        stewards_fph_blob = pickle.dumps(stewards_fph_list)
        update_str = "UPDATE " + table \
                   + " SET stewards_fph_list = ? WHERE entity_fph = ?"
        cursor.execute(update_str, stewards_fph_list)

        select_str = "SELECT stewardships_fph_list FROM agents " \
                   + " WHERE entity_fph = ?"
        cursor.execute(select_str, (entity_fph,))
        stewardships_fph_blob = cursor.fetchone()[0]
        stewardships_fph_list = pickle.loads(stewardships_fph_blob)
        stewardships_fph_list.remove(agent_fph)
        stewardships_fph_blob = pickle.dumps(stewardships_fph_list)
        update_str = "UPDATE agents SET stewardships_fph_list = ? " \
                   + "WHERE entity_fph = ?"
        cursor.execute(update_str, stewardships_fph_list)

        conn.commit()
        cursor.close()

    return ""

#------------------------------------------------------------------------------
# List stewards of a namespace or currency:

def list_stewards(entity_fph):

    if not re_fph.match(entity_fph):
        return [], entity_fph + " is not an FPH"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        etype = get_entity_type(entity_fph)
        if etype == "namespace":
            table = "namespaces"
        elif etype == "currency":
            table = "currencies"
        else:
            return [], "Invalid entity type"

        select_str = "SELECT stewards_fph_list FROM " + table \
                   + " WHERE entity_fph = ?"
        cursor.execute(select_str, (entity_fph,))
        stewards_fph_blob = cursor.fetchone()[0]
        cursor.close()

        stewards_fph_list = pickle.loads(stewards_fph_blob)
        stewards = []
        for steward_fph in stewards_fph_list:
            stewards.append(steward_fph)

    return stewards, ""

#------------------------------------------------------------------------------
# List stewardships of aagent:

def list_stewardships(agent_fph):

    if not re_fph.match(agent_fph):
        return [], agent_fph + " is not an FPH"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        select_str = "SELECT stewardships_fph_list FROM agents " \
                   + " WHERE entity_fph = ?"
        cursor.execute(select_str, (agent_fph,))
        stewardships_fph_blob = cursor.fetchone()[0]
        cursor.close()

    stewardships_fph_list = pickle.loads(stewardships_fph_blob)
    stewardships = []
    for stewardhip_fph in stewardships_fph_list:
        stewardships.append(stewardhip_fph)

    return stewardships, ""


#==============================================================================
# Authentication and login managemenet:

def register_authenticated_login(agent_fph):
    if not re_fph.match(agent_fph):
        return False, "", agent_fph + " is not an FPH"
    entity_type = get_entity_type(agent_fph)
    if entity_type == "secid":
        primid_fph = get_primid(agent_fph)
        login_id_fph = agent_fph
    elif entity_type == "primid":
        primid_fph = agent_fph
        login_id_fph = agent_fph
    else:
        return False, "", agent_fph + " is not an agent FPH"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO logins (primid_fph, login_id_fph, login_authenticated)
            VALUES (?, ?, ?)
            """,
            (primid_fph, login_id_fph, True)
        )
        conn.commit()
        cursor.close()
    return primid_fph, login_id_fph, ""


#------------------------------------------------------------------------------
def deregister_authenticated_login(primid_fph):
    if not re_fph.match(agent_fph):
        return False, agent_fph + " is not an FPH"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            DELETE FROM login WHERE primid_fph = ?
            """,
            (primid_fph,)
        )
        conn.commit()
        cursor.close()
    #return primid_fph, login_id_fph


#------------------------------------------------------------------------------
def check_authenticated_login(agent_fph):
    #if not re_fph.match(agent_fph):
    #    return False, "", agent_fph + " is not an FPH"
    entity_type = get_entity_type(agent_fph)
    if entity_type == "secid":
        primid_fph = get_primid(agent_fph)
    elif entity_type == "primid":
        primid_fph = agent_fph
    else:
        return False
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT login_authenticated FROM login WHERE primid_fph = ?
            """,
            (primid_fph,)
        )
        result = cursor.fetchone()
        login_authenticated = result[0]
        #login_id_fph = result[1]
    return login_authenticated



#------------------------------------------------------------------------------

def get_auth_data(agent_fph):
    if not re_fph.match(agent_fph):
        return {}, agent_fph + " is not an FPH"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT entity_type, password_hash, pin, access_token_hash
            FROM agents WHERE entity_fph = ?
            """,
            (agent_fph,)
        )
        auth_dict = {}
        result = cursor.fetchone()
    if result[0] not in ["primid", "secid", "agent"]:
        return {}, agent_fph + " is not an FPH"
#    auth_dict["entity_type"] = result[0]
    auth_dict["password_hash"] = result[1]
    auth_dict["pin"] = result[2]
    auth_dict["access_token_hash"] = result[3]
    return auth_dict, ""


#==============================================================================
# List existing namespaces, specifying optionally a parent namespace.

def list_active_namespaces(ancestor_namespace_identifier = ""):

    if ancestor_namespace_identifier == "": # universal root namespace
        ancestor_fph = UNIVERSAL_ROOT_FPH
        ancestor_hrns = ""
        entity_type = "namespace"
        m = ""
    else:
        ancestor_fph, \
        ancestor_hrns, \
        entity_type, \
        m = identify_entity(ancestor_namespace_identifier)
    if m:
        return [], m

    # First the namespace trees are selected where the root namespace is active
    # and has the specified ancestor namespace as its parent:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT entity_fph, active FROM namespaces;")
        result_list = cursor.fetchall()

    # At this point we have a list of active namespaces sharing a specified
    # parent. Some of which will have descendants, and from among these the
    # remaining active namespaces will have to be identified.
    #
    namespace_fph_list = []
    for result in result_list:
        if result[1]: # namespace is active
            namespace_hrns = fph_to_hrns(result[0])
            if namespace_hrns.replace("." + ancestor_hrns, "") != "":
                namespace_fph_list.append(result[0])
    return namespace_fph_list, ""


#==============================================================================
# List agents:
#
# NOTE: The agents' "active" field (integer) should be replaced with a "status"
#       field (test).

def list_agents(status = "active"):

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT entity_fph, active FROM agents;")
        result_list = cursor.fetchall()

    agent_fph_list = []
    for result in result_list:
        if status == "all":
            agent_fph_list.append(result[0])
        elif status == "active":
            if result[1]: # the identity is active
                agent_fph_list.append(result[0])
        else:
            return [], "Not yet implemented"

    return agent_fph_list, ""

#==============================================================================
