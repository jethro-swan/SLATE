import sqlite3
#import random
import os
import pickle

from app.core.constants import ENTITIES_DB
from app.core.constants import SUBSTRATE_FPH
from app.core.common import nshash
from app.core.regexp_list import *
from app.core.slate_core import hrns_to_fph, fph_to_hrns
from app.core.slate_core import register_identifier
from app.core.slate_core import register_entity_type
from app.core.slate_core import new_account
from app.core.slate_core import new_namespace
from app.core.slate_core import identify_entity
from app.core.auth import auth_hash
from app.core.cctld_list import *

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
#   currencies. For simplicity, this is given the name "cc".
#
#   A primid (primary identity) to serve as the initial steward of the first
#   namespace or currency created after installation.
#
#   This primid is also the initial steward of all of the the geographical root
#   namespaces create during installation. It belongs (at least initially) to
#   the system adminstrator who creates the NESTS hub.
#
#   The default name (HRNS) of this primid is "adm.cc".
#
# - A currency (cc in scope) which can be can be used to create the initial
#   accounts for the first new primids created. The default name (HRNS) of this
#   currency is "hrs.cc" and its default initial steward's HRNS for this is
# "adm.cc".
#
# - When the initial primid "adm.cc" is created, an account with HRNS
#   "hrs.adm.cc" is created for it in the currency "hrs.cc" (the default
# currency for identities created within the "cc" namespace).

def create_seed_entities():

    # (In due course, the default values for the following will be read from a
    # configuration file.)

    # Default values:
    seed_primid_realname        = "Gaia"
    seed_primid_email_1         = "gaia@lrc.org.uk"
    seed_primid_email_2         = ""
    seed_primid_password        = "Gl0balM3ltd0wn"
    seed_primid_pin             = "123456"
    seed_primid_access_token    = "1a1b2c3d5e8f13e21f34d55c89b144ff"

    # Override values if defined:
    fname = os.getcwd() + "/seed_primid_details.txt"
    with open(fname, "r") as f:
        primid_details = f.readlines()
    for line in primid_details:
        l = line.split("=")
        if l[0].strip() == "seed_primid_realname":
            seed_primid_realname = l[1].strip()
        elif l[0].strip() == "seed_primid_email_1":
            seed_primid_email_1 = l[1].strip()
        elif  l[0].strip() == "seed_primid_email_2":
            seed_primid_email_2 = l[1].strip()
        elif  l[0].strip() == "seed_primid_password":
            seed_primid_password = l[1].strip()
        elif l[0].strip() == "seed_primid_pin":
            seed_primid_pin = l[1].strip()
        elif l[0].strip() == "seed_primid_access_token":
            seed_primid_access_token = l[1].strip()


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
    #     "cc".


    # 2025-04-06: Changes to accommodate use of any entity identifier as a
    # *namespace* identifier, e.g.
    #   cc  as both seed *namespace* and seed *currency*
#    seed_namespace_hrns     = "cc"
    seed_currency_hrns      = "cc"
    seed_primid_hrns        = "cc"
    seed_primid_hrns        = "adm.cc"
    seed_account_hrns       = "cc.adm.cc"

    # Seed entities (see https://nests.lrc.org.uk/entity_dependencies.html)
    # by HRNS:
    # Previous version:
#    seed_namespace_hrns     = "cc"
#    seed_currency_hrns      = "hrs.cc"
#    seed_primid_hrns        = "adm.cc"
#    seed_account_hrns       = "hrs.adm.cc"





    # The *substrate* is the nameless *namespace* from which all others ramify,
    # the parent *namespace* of all "root" *namespace* (such as "cc"). This has
    # already been added to the FPH>HRNS map (at the point of its creation
    # - see fph_hrns_maps.py).
    substrate_hrns = ""
    #substrate_fph = nshash("")
#    substrate_fph, m = hrns_to_fph(substrate_hrns) ### 2025-04-26
#    if m:
#        print("Problem mapping substrate HRNS (\"\") to FPH")



    # The seed entities are now added to the FPH>HRNS map:

#    seed_namespace_fph, m       = hrns_to_fph(seed_namespace_hrns)
#                                # parent namespace: "" (the *substrate*)
#                                # initial steward:  "adm.cc"

#    seed_currency_fph, m        = hrns_to_fph(seed_currency_hrns)
    #seed_currency_parent_hrns   = "cc"
#    seed_currency_parent_fph    = SUBSTRATE_FPH
                                # initial steward:  "adm.cc"

#    seed_namespace_fph = seed_currency_fph



#    seed_primid_fph, m          = hrns_to_fph(seed_primid_hrns)
#    seed_primid_parent_hrns     = "cc"
                                # initial account:  "hrs.adm.cc"
                                # stewardships:     "cc" (namespace)
                                #                   "hrs.cc" (currency)

#    seed_account_fph, m         = hrns_to_fph(seed_account_hrns)
#    seed_account_parent_hrns    = "adm.cc"
                                # owned by:         "adm.cc"
                                # in currency:      "hrs.cc"

    # Every *namespace* or *currency* needs a set of stewards. At this point
    # only one *primid* ("adm.cc") exists so, for the time being, this
    # must serve as the sole steward for the "cc" *namespace* and the
    # "hrs.cc" *currency*.
    #stewards_fph_list       = [seed_primid_fph]
    #stewards_fph_blob       = pickle.dumps(stewards_fph_list)
    #
    # The these stewardships must be added to the seed *primid* ("adm.cc"):
    #stewardships_fph_list   = [seed_namespace_hrns, seed_currency_hrns]
    #stewardships_fph_blob   = pickle.dumps(stewardships_fph_list)
    #
    # (In SLATE, these FPH lists are saved in SQLite as blobs, for which reason
    # they must be serialized. In NESTS, they are saved as simple text files.

    # The seed *account* ("hrs.adm.cc") is in the seed *currency*
    # ("hrs.cc"):
    #account_currency_fph    = seed_currency_fph
    # An *account* can obviously have only one *currency*, so this does not
    # have to be saved as a serialized list.
    #
    # At this point, the seed *currency* ("hrs.cc") has only one
    # *account* ("hrs.adm.cc"):
    #currency_accts_fph_list = [seed_account_fph]
    #currency_accts_fph_blob = pickle.dumps(currency_accts_fph_list)


    #seed_account_currency_fph = seed_currency_fph
#    seed_stewardship_1_fph  = seed_namespace_fph
#    seed_stewardship_2_fph  = seed_currency_fph

    #seed_primid_account_fph = [seed_account_fph]
#    seed_primid_account_fph = seed_account_fph
    #seed_primid_accts_fph_blob   = pickle.dumps(seed_primid_accts_fph_list)

    # NB  There is no need for a seed *secid*

    # First the common proprties entries are created:

    #--------------------------------------------------------------------------
    # Seed *namespace*: "cc"
    #
    # NB  The *namespace* "cc" is a "root" *namespace*. Therefore it has no
    #     named parent *namespace*.

    seed_namespace_hrns = "cc"
    seed_currency_hrns = "cc"
    seed_primid_hrns        = "adm.cc"
    seed_account_hrns       = "cc.adm.cc"

    seed_primid_fph = register_identifier(seed_primid_hrns)
    register_entity_type(seed_primid_fph, "primid")

    seed_account_fph = register_identifier(seed_account_hrns)
    register_entity_type(seed_account_fph, "account")

    seed_currency_fph = register_identifier(seed_currency_hrns)
    register_entity_type(seed_currency_fph, "currency")

    seed_namespace_fph = register_identifier(seed_namespace_hrns)
    register_entity_type(seed_namespace_fph, "namespace")

    #--------------------------------------------------------------------------
    # Seed *account*:

    # The seed *account* type-specific properties are added:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accounts (" \
                + "entity_fph, " \
                + "account_owner_fph, " \
                + "account_currency_fph, " \
                + "account_balance" \
            + ") VALUES (?, ?, ?, ?)",
            (
                seed_account_fph,
                seed_primid_fph,
                seed_currency_fph,
                0
            )
        )
        conn.commit()
        cursor.close()

    print("seed_account_fph  = " + seed_account_fph)
    print("seed_primid_fph   = " + seed_primid_fph)
    print("seed_currency_fph = " + seed_currency_fph)

    #--------------------------------------------------------------------------
    # Seed *primid*:

    # Then seed *primid* type-specific properties are added:
    accounts_fph_list = []
    accounts_fph_list.append(seed_account_fph)

    nstewardships_fph_list = []
    nstewardships_fph_list.append(seed_namespace_fph)
    cstewardships_fph_list = []
    cstewardships_fph_list.append(seed_currency_fph)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO primids (" \
                + "entity_fph, " \
                + "primid_realname, " \
                + "primid_email_1_hash, " \
                + "primid_email_2_hash, " \
                + "secids_fph_list, " \
                + "accounts_fph_list, " \
                + "nstewardships_fph_list, " \
                + "cstewardships_fph_list, " \
                + "password_hash, " \
                + "pin, " \
                + "access_token_hash" \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                seed_primid_fph,
                seed_primid_realname,
                auth_hash(seed_primid_email_1),
                auth_hash(seed_primid_email_2),
                pickle.dumps([]),
                pickle.dumps(accounts_fph_list),
                pickle.dumps(nstewardships_fph_list),
                pickle.dumps(cstewardships_fph_list),
                auth_hash(seed_primid_password),
                seed_primid_pin,
                auth_hash(seed_primid_access_token)
            )
        )
        conn.commit()
        cursor.close()



    #--------------------------------------------------------------------------
    # The seed *namespace* and *currency* specific properties are added:

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO currencies (" \
                + "entity_fph, " \
                + "currency_prefix, " \
                + "currency_suffix, " \
                + "default_account_name, " \
                + "stewards_fph_list " \
            + ") VALUES (?, ?, ?, ?, ?)",
            (
                seed_currency_fph,
                "",         # currency prefix
                "",        # currency suffix
                "cc",    # default *account* name
                pickle.dumps([seed_primid_fph]) # first steward added to list
            )
        )
        # NB: The following may not be needed, given that the *currency* and
        #     *account* FPH are both stored in the "accounts" table, but for
        #     the time being there is no need to remove this step.
        cursor.execute(
            "INSERT INTO currency_accounts (" \
                + "currency_fph, " \
                + "account_fph " \
            + ") VALUES (?, ?)",
            (
                seed_currency_fph,
                seed_account_fph
            )
        )
        conn.commit()
        cursor.close()

    #seed_account_currency_fph = seed_currency_fph
    seed_stewardship_1_fph  = seed_namespace_fph
    seed_stewardship_2_fph  = seed_currency_fph



#==============================================================================
# A set of "pseudo-TLD" root namespaces, each having the same null parent
# nameaspace ("": substrate_fph) and the same initial steward ("adm.cc":
# seed_primid_fph):

def create_quasitld_set(full = False):

    if full:
        cctld_list_here = cctld_list
    else:
        cctld_list_here = cctld_reduced_list

    # These are recreated here in case it is necessary to callthis function
    # before create_seed_entities( ).
    substrate_fph = nshash("")
    seed_primid_fph = nshash("adm.cc")
##    seed_currency_fph = nshash("hrs.cc")
    seed_currency_fph = nshash("cc")

    errors = "\n"
    tld_fph_list = []
    for tld in cctld_list_here:
        namespace_fph, \
        namespace_hrns, \
        m = new_namespace(
                tld,
                substrate_fph,
                seed_currency_fph,
                seed_primid_fph
            )
        if m:
            print(m)
        errors += m + "\n"
        tld_fph_list.append(namespace_fph)

    return tld_fph_list, errors


# A set of single-letter sandbox root *namespaces* is created:
def create_sandbox_root_set():

    # These are recreated here in case it is necessary to call this function
    # before create_seed_entities( ).
    s_fph = register_identifier("s")
    register_entity_type(s_fph, "namespace")

##    seed_primid_fph, m  = hrns_to_fph("adm.cc")
##    seed_currency_fph, m  = hrns_to_fph("hrs.cc")
##    seed_currency_fph, m  = hrns_to_fph("cc")

    errors = "\n"
    fph_of = {}
    for s in ["s", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]:
        namespace_fph, \
        namespace_hrns, \
        m = new_namespace(s, s_fph, seed_currency_fph, seed_primid_fph)
        if m:
            print(s + ": ", end="")
            print(m)

        print(namespace_fph + " > " + namespace_hrns)

        fph_of[namespace_hrns] = namespace_fph
        errors += m + "\n"

    return fph_of, errors



#==============================================================================
