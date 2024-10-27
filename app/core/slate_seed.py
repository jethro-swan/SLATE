import sqlite3
#import random
#import os
import pickle

from .constants import ENTITIES_DB
from .common import nshash
from .regexp_list import *
from .slate_core import hrns_to_fph
from .slate_core import add_entity_common_properties
from .slate_core import new_account
from .slate_core import new_namespace
#from .slate_core import add_namespace_specific_properties
#from .slate_core import add_account_specific_properties
from .cctld_list import *

debugging = True

#==============================================================================
# The initial (minimal) set of entities created in a SLATE node are constrained
# by dependency rules similar to those in NESTS although slightly simpler
# because
# (a) there atr two classes of agent (primid and secid);
# (b) there is only one namespace separator (".");
# (c) only the Latin alphabet is used; and
# (b) there is only one class of currency (money).
# (see https://nests.lrc.org.uk/entity_dependencies.html
#
# Every SLATE or NESTS installation must be provided with a minimal set of
# pre-existing entities:
#
# - A namespace to be the parent both of the initial agents and the initial
#   currencies. For simplicity, this is given the name "global".
#
#   A primid (primary identity) to serve as the initial steward of the first
#   namespace or currency created after installation.
#
#   This primid is also the initial steward of all of the the geographical root
#   namespaces create during installation. It belongs (at least initially) to
#   the system adminstrator who creates the NESTS hub.
#
#   The default name (HRNS) of this primid is "gaia.global".
#
# - A currency (global in scope) which can be can be used to create the initial
#   accounts for the first new primids created. The default name (HRNS) of this
#   currency is "hours.global" and its default initial steward's HRNS for this
#   is "gaia.global".
#
# - When the initial primid "gaia.global" is created, an account with HRNS
#   "hours.gaia.global" is created for it in the currency "hours.global" (the
#   default currency for identities created within the "global" namespace).

def create_seed_entities():

    # (In due course, the default values for the following will be read from a
    # configuration file.)
    seed_primid_realname        = "Gaia"
    seed_primid_email_1         = "gaia@lrc.org.uk"
    seed_primid_email_2         = ""
    seed_primid_password        = "Gl0balM3ltd0wn"
    seed_primid_pin             = "123456"
    seed_primid_access_token    = "1a1b2c3d5e8f13e21f34d55c89b144ff"


    # A note on namespaces:
    #
    # The name of every entity, of whatever type, is contained within a
    # namespace.
    #
    # Namespaces fall into three categories:
    # (1) The term *namespace* is generally used to mean a non-terminal
    #     namespace that can contain the name of any type of entity.
    # (2) The name of an agent (whether a *primid* or a *secid*) identifies a
    #     special type of namespace (a "terminal" *namespace*) that can contain
    #     only the names of *accounts*.
    # (3) A *root namespace* is one the name of which is not contained within
    #     a named *namespace*. Such *root namespace* all share an unnamed
    #     namespace ("") which contains only the names of *root namespaces*,
    #     which include (typically) geographical containers (such as "uk",
    #     "ca", "es", "de", "fr", etc.) or containers having a different
    #     significance.
    #     The first *root namespace* created (the "seed namespace") is named
    #     "global".

    # Seed entities (see https://nests.lrc.org.uk/entity_dependencies.html)
    # by HRNS:
    root_hrns = ""          # The nameless namespace from which all others
                            # ramify.
    seed_namespace_hrns     = "global"
                            # parent namespace:     ""
                            # initial steward:      "gaia.global"

    seed_currency_hrns      = "hours.global"
    seed_currency_fph, m    = hrns_to_fph(seed_currency_hrns)
    seed_currency_parent_ns = "global"
                            # initial steward:      "gaia.global"

    seed_primid_hrns        = "gaia.global"
    seed_primid_fph, m      = hrns_to_fph(seed_primid_hrns)
    seed_primid_parent_ns   = "global"
                            # initial account:      "hours.gaia.global"
                            # stewardships:         "global" (namespace)
                            #                       "hours.global" (currency)

    seed_account_hrns       = "hours.gaia.global"
    seed_account_fph, m     = hrns_to_fph(seed_account_hrns)
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
    seed_primid_fph, m      = hrns_to_fph(seed_primid_hrns)

    # Every *namespace* or *currency* needs a set of stewards. At this point
    # only one *primid* ("gaia.global") exists so, for the time being, this
    # must serve as the sole steward for the "global" *namespace* and the
    # "hours.global" *currency*.
    #stewards_fph_list       = [seed_primid_fph]
    #stewards_fph_blob       = pickle.dumps(stewards_fph_list)
    #
    # The these stewardships must be added to the seed *primid* ("gaia.global"):
    #stewardships_fph_list   = [seed_namespace_hrns, seed_currency_hrns]
    #stewardships_fph_blob   = pickle.dumps(stewardships_fph_list)
    #
    # (These FPH lists are saved in SQLite as blobs, for which reason they must
    # be serialized.)

    # The seed *account* ("hours.gaia.global") is in the seed *currency*
    # ("hours.global"):
    #account_currency_fph    = seed_currency_fph
    # An *account* can obviously have only one *currency*, so this does not
    # have to be saved as a serialized list.
    #
    # At this point, the seed *currency* ("hours.global") has only one
    # *account* ("hours.gaia.global"):
    #currency_accts_fph_list = [seed_account_fph]
    #currency_accts_fph_blob = pickle.dumps(currency_accts_fph_list)


    #seed_account_currency_fph = seed_currency_fph
    seed_stewardship_1_fph  = seed_namespace_fph
    seed_stewardship_2_fph  = seed_currency_fph

    #seed_primid_account_fph = [seed_account_fph]
    seed_primid_account_fph = seed_account_fph
    #seed_primid_accts_fph_blob   = pickle.dumps(seed_primid_accts_fph_list)

    # NB  There is no need for a seed *secid*

    # First the common proprties entries are created:

    #--------------------------------------------------------------------------
    # Seed *namespace*:
    add_entity_common_properties(
        seed_namespace_fph,     # NB  The namespace "global" is a special case
        root_fph,               #     in that it has no parent namespace.
        "namespace",
        True
    )
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO namespaces (
                entity_fph,
                stewards_fph_list
            )
            VALUES (?, ?)
            """,
            (
                seed_namespace_fph,
                pickle.dumps([seed_primid_fph])
            )
        )
        conn.commit()
        cursor.close()

    #--------------------------------------------------------------------------
    # Seed *currency*:
    add_entity_common_properties(
        seed_currency_fph,
        nshash(seed_currency_parent_ns),
        "currency",
        True
    )
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
                seed_currency_fph,
                "",     # currency prefix
                "h",    # currency suffix
                pickle.dumps([seed_primid_fph])   # first steward added to list
            )
        )
        cursor.execute(
            """
            INSERT INTO currency_accounts (
                currency_fph,
                account_fph
            )
            VALUES (?, ?)
            """,
            (
                seed_currency_fph,
                seed_account_fph
            )
        )
        conn.commit()
        cursor.close()

    #--------------------------------------------------------------------------
    # Seed *primid*:
    add_entity_common_properties(
        seed_primid_fph,
        nshash(seed_primid_parent_ns),
        "primid",
        True
    )
    # Then the type-specific properties are added:

    # The seed *account* is created
    # in the seed *currency*
    # FOR the seed *primid*:
    seed_account_fph, \
    seed_account_hrns, \
    m = new_account(seed_account_hrns, seed_primid_fph, seed_currency_fph)
    if m:
        return m

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO primids (
                entity_fph = ?,
                primid_realname = ?,
                primid_email_1 = ?,
                primid_email_2 = ?,
                accounts_fph_list = ?,
                stewardships_fph_list = ?,
                password_hash = ?,
                pin = ?,
                access_token_hash = ?
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                seed_primid_fph,
                seed_primid_realname,
                seed_primid_email_1,
                seed_primid_email_2,
                pickle.dumps([seed_account_fph]),
                pickle.dumps([seed_namespace_fph, seed_currency_fph]),
                auth_hash(seed_primid_password),
                seed_primid_pin,
                auth_hash(seed_primid_access_token)
            )
        )
        conn.commit()
        cursor.close()


#==============================================================================
# A set of "pseudo-TLD" root namespaces, each having the same null parent
# nameaspace ("": root_fph) and the same initial steward ("gaia.global":
# seed_primid_fph):

def create_quasitld_set(full = False, display = False):

    if full:
        cctld_list_here = cctld_list
    else:
        cctld_list_here = cctld_reduced_list

    # This is a crude progress counter to indicate the sequence in which random
    # entities are created or an HRNS collision detected.
    progress_count = 80

    root_fph = nshash("")
    seed_primid_fph = nshash("gaia.global")
    for tld in cctld_list_here:
        namespace_fph, namespace_hrns, m = new_namespace(
                                               tld,
                                               root_fph,
                                               seed_primid_fph
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
