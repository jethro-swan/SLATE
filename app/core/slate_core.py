import sqlite3
import random
import os
import pickle
from pathlib import Path

from constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
from constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from common import filename_timestamp as timestamp
from common import nshash
from fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from dbm_functions import dbm_create_map
from auth import auth_hash
from regexp_list import *
from unix_functions import fcopy

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
        # Create agents table:
        cursor.execute("""
    	    CREATE TABLE IF NOT EXISTS agents (
                agent_fph TEXT PRIMARY KEY,
                agent_realname TEXT,
                agent_email TEXT NOT NULL,
                accounts_fph_list BLOB,
                stewardships_fph_list BLOB,
                password_hash TEXT NOT NULL,
                pin TEXT,
                active INTEGER NOT NULL
            );"""
        )
        # Create currencies table:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS currencies (
                currency_fph TEXT PRIMARY KEY,
                currency_prefix TEXT,
                currency_suffix TEXT,
                accounts_fph_list BLOB,
                stewards_fph_list BLOB,
                active INTEGER NOT NULL
            );"""
        )
        # Create accounts table:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                account_fph TEXT PRIMARY KEY,
                account_owner_fph TEXT NOT NULL,
                account_currency_fph TEXT NOT NULL,
                account_balance INTEGER NOT NULL DEFAULT 0,
                active INTEGER NOT NULL
            );"""
        )
        # Create namespaces table:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS namespaces (
                namespace_fph TEXT PRIMARY KEY,
                stewards_fph_list TEXT NOT NULL,
                active INTEGER NOT NULL
            );"""
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
                            # parent namespace:     "global"
                            # initial steward:      "gaia.global"

    seed_agent_hrns         = "gaia.global"
                            # parent namespace:     "global"
                            # initial account:      "hours.gaia.global"
                            # stewardships:         "global" (namespace)
                            #                       "hours.global" (currency)

    seed_account_hrns       = "hours.gaia.global"
                            # parent namespace:     "gaia.global"
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
    s_agent_realname        = "Gaia"
    s_agent_email           = "gaia@lrc.org.uk"
    s_agent_password        = "Gl0balM3ltd0wn"
    s_agent_password_hash   = auth_hash(s_agent_password)
    s_agent_pin             = "123456"

    # Seed agent's initial account:
    #seed_agent_acct_hrns = "hours.gaia.global"
    #seed_agent_accts_fph, m = hrns_to_fph(seed_agent_acct_hrns)
    s_agent_accts_fph_list  = [seed_acct_fph]
    s_agent_accts_fph_blob  = pickle.dumps(s_agent_accts_fph_list)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO agents (
                agent_fph,
                agent_realname,
                agent_email,
                accounts_fph_list,
                stewardships_fph_list,
                password_hash,
                pin,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                seed_agent_fph,
                s_agent_realname,
                s_agent_email,
                s_agent_accts_fph_blob,
                stewardships_fph_blob,
                s_agent_password_hash,
                s_agent_pin,
                True
            )
        )

        cursor.execute("""
            INSERT INTO currencies (
                currency_fph,
                currency_prefix,
                currency_suffix,
                accounts_fph_list,
                stewards_fph_list,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                seed_currency_fph,
                "",
                "h",
                currency_accts_fph_blob,
                stewards_fph_blob,
                True
            )
        )

        cursor.execute("""
            INSERT INTO namespaces (
                namespace_fph,
                stewards_fph_list,
                active
            )
            VALUES (?, ?, ?)""",
            (
                seed_namespace_fph,
                stewards_fph_blob,
                True
            )
        )

        # NB The namespace "global" is a special case in that it has no parent
        #    namespace.

        cursor.execute("""
            INSERT INTO accounts (
                account_fph,
                account_owner_fph,
                account_currency_fph,
                account_balance,
                active
            )
            VALUES (?, ?, ?, ?, ?)""",
            (
                seed_acct_fph,
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
        return "", "", account_hrns + " exists already"

    account_fph, m = hrns_to_fph(account_hrns)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accounts (
                account_fph,
                account_owner_fph,
                account_currency_fph,
                account_balance,
                active
            )
            VALUES (?, ?, ?, ?, ?)""",
            (
                account_fph,
                agent_fph,
                currency_fph,
                0,
                True
            )
        )
        conn.commit()
        cursor.close()

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
        return "", "", "Invalid parent namespace FPH: " + parent_namespace_fph

    if not re_fph.match(initial_currency_fph):
        return "", "", "Invalid initial currency FPH: " + initial_currency_fph

    namespace_hrns = fph_to_hrns(parent_namespace_fph)
    agent_hrns = username + "." + namespace_hrns

    if fph_to_hrns(nshash(agent_hrns)):
        return "", "", agent_hrns + " exists already"

    agent_fph, m = hrns_to_fph(agent_hrns)

    if not re_email.match(email_address):
        return("Invalid email address. Agent not created.")

    password_hash = auth_hash(password)

    account_fph, account_hrns, m = new_account(agent_fph, initial_currency_fph)

    accounts_fph_list = pickle.dumps([account_fph])
    stewardships_fph_list = pickle.dumps([])

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO agents (
                agent_fph,
                agent_realname,
                agent_email,
                accounts_fph_list,
                stewardships_fph_list,
                password_hash,
                pin,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                agent_fph,
                realname,
                email_address,
                accounts_fph_list,
                stewardships_fph_list,
                password_hash,
                pin,
                True
            )
        )
        conn.commit()
        cursor.close()

    return agent_fph, agent_hrns, ""

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
    namespace_hrns = namespace_name + "." + parent_namespace_hrns

    if fph_to_hrns(nshash(namespace_hrns)):
        return "", "", namespace_hrns + " exists already"

    namespace_fph, m = hrns_to_fph(namespace_hrns)

    stewards_fph_blob = pickle.dumps(list([initial_steward_fph]))

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO namespaces (
                namespace_fph,
                stewards_fph_list,
                active
            )
            VALUES (?, ?, ?)""",
            (
                namespace_fph,
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
        return "", "", currency_hrns + " exists already"

    currency_fph, m = hrns_to_fph(currency_hrns)

    initial_steward_hrns = fph_to_hrns(initial_steward_fph)
    initial_account_hrns = currency_name + "." + initial_steward_hrns
    initial_account_fph, m = hrns_to_fph(initial_account_hrns)
    accounts_fph_list = pickle.dumps([initial_account_fph])

    stewards_fph_list = pickle.dumps([initial_steward_fph])

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO currencies (
                currency_fph,
                currency_prefix,
                currency_suffix,
                accounts_fph_list,
                stewards_fph_list,
                active
            )
            VALUES (?, ?, ?, ?, ?, ?)""",
            (
                currency_fph,
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

def get_accounts(agent_fph):
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT accounts_list FROM agents WHERE agent_fph = ?;
        """)
        accounts_fph_blob = cursor.fetchone()
        cursor.close()
    accounts_fph_list = pickle.loads(accounts_fph_blob)

    return accounts_fph_list    # list


def get_currencies(agent_fph): # in which an agent has accounts

    return currencies_fph_list    # list


def get_account(agent_fph, currency_fph): # which the agent has for the currency

    return account_fph


def get_parent_namespace(entity_fph): # for any entity

    return namespace_fph # string


#def get_child_namespaces(namespaces_fph):
#
#    return namespace_fph_list # list

# Get the entity type:
def get_entity_type(entity_fph):

    return entity_type # string


# List all namespaces immediately below a specified namespace:
def list_child_namespaces(namespace_fph):

    return namespace_fph_list # list


# List all namespaces anywhere in the tree below the specified root namespace:
def list_all_namespaces(root_namespace_fph):

    return namespace_fph_list # list


# List all currencies named within the specified namespace:
def list_currencies(namespace_fph):

    return currency_fph_list # list


# List all agents named within the specified namespace:
def list_agents(namespace_fph):

    return agent_fph_list # list


# List all accounts belong to the specified agent:
def list_accounts(agent_fph):

    return account_fph_list # list




# List the FPH of the currencies in which two agents both have an account:
def list_currencies_in_common_by_fph(a1_fph, a2_fph):
    return list(set(get_currencies(a1_fph)) & set(get_currencies(a2_fph)))

# List the HRNS of the currencies in which two agents both have an account:
def list_currencies_in_common_by_hrns(a1_fph, a2_fph):
    for currency_fph in list_currencies_in_common_by_fph(a1_fph, a2_fph):
        print(fph_to_hrns(currency_fph))

#==============================================================================
