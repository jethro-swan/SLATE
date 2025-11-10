import sqlite3
import os
import pickle

from app.core.constants import IDENTIFIERS_DB, ENTITIES_DB
from app.core.constants import SUBSTRATE_FPH
from app.core.common import nshash
from app.core.regexp_list import *
#from app.core.slate_core import hrns_to_fph, fph_to_hrns, record_parent
from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
#from app.core.fph_hrns_maps import record_parent
from app.core.slate_core import record_parent
#from app.core.fph_hrns_maps import record_private_namespace_root
from app.core.slate_core import record_private_namespace_root
from app.core.slate_core import register_identifier
from app.core.slate_core import register_entity_type
from app.core.slate_core import new_account
from app.core.slate_core import new_namespace
from app.core.slate_core import new_currency
from app.core.slate_core import identify_entity
from app.core.slate_core import complete_parent_namespace
from app.core.auth import auth_hash
from app.core.cctld_list import *

#==============================================================================
# The initial (minimal) set of entities created in a SLATE node are constrained
# by dependency rules similar to those in NESTS although slightly simpler
# because
# (1) there is currenctly only one tested *namespace* separator (".");
# (2) only the Latin alphabet is used; and
# (3) there is only one class of *currency* (money).

# A note on namespaces:
#
# The name of every entity, of whatever type, is prefixed to the identifier of
# an existing *namespace*. Namespaces fall into three categories:
# (1) The term *namespace* is generally used to mean a non-terminal
#     *namespace* that can contain the name of any type of entity.
# (2) The identifier of an agent (whether a *primid*, and *ahid" or a *secid*)
#     identifies the root of a private *namespace*.
# (3) A *root namespace* is one the ancestor of which is identified by an empty
#     string (""). The *root namespaces* may include (typically) geographical
#     containers (such as "uk", "ca", "es", "de", "fr", etc.) or containers
#     having a different significance. The first *root namespace* created (the
#     "seed namespace") has the identifier "cc".

# Entity dependency
#
# The entity dependency rules for both SLATE and the (revised version of) NESTS
# are essentially as summarized here:
#
# Agents: There are three classes of agent (*primid*, *ahid* and *secid*):
# (1) A *primid* (a.k.a. *login identity*) is the unique identifier
#     anchoring the agent in the real world. Each *primid* may have any
#     number of *ahid* or *secid*.
# (2) An *ahid* (*account-hilder identity*) can be paired with any number of
#     distinct *currencies*, each such pairing indexing an *account*. Each
#     *ahid* has one *primid*.
# (3) A *secid* (where used) can serve as an alias to anchor a *primid* in
#     any number of *namespaces* (where authorized). A *secid* can hold any
#     number of *accounts* but, in contrast to an *ahid*, is not itself used
#     to identify those in a pairing. Each *secid* has one *primid*.
#
# All *root namespaces* share a nameless ancestor (the substrate) which has an
# FPH but an empty HRNS. Uniquely, the substrate id its own ancestor.
#
# For details, see https://nests.lrc.org.uk/entity_dependencies.html
#
# Every SLATE or NESTS installation must be provided with a minimal set of
# pre-existing entities:
#
# - A *namespace* to be the parent both of the initial agents and the initial
#   currencies. For simplicity, this is given the name "cc".
#
# - A *primid* (*primary identity* or *login identity*) to serve as the initial
#   steward of the first *namespace* or *currency* created after installation.
#
#   This *primid* is also the initial steward of all of the the geographical
#   root *namespaces* create during installation. It belongs (at least
#   initially) to the system adminstrator who creates the SLATE/NESTS hub.
#
#   The default name (HRNS) of this *primid* is "cc".
#
# - A *currency* (cc) which can be can be used to create the initial *accounts*
#   for the first new *ahids* created. The default name (HRNS) of this
#   *currency* is "cc" and its default initial steward is "adm.cc".
#
# - When the initial *primid* is created, an *account*, a *namespace*, an
#   *ahid* and a *currency* are created with the same identifier.

def create_substrate():
    # The substrate is unique in that
    # (a) its parent has no HRNS
    # (b) it serves as its own parent *namespace*
    # (c) its identifier has only one registered entity type (*namesapce*)
    with sqlite3.connect(IDENTIFIERS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO entities_registered (" \
            + "entity_fph, parent_fph, " \
            + "namespace, currency, account, primid, ahid" \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?)",
            (SUBSTRATE_FPH, SUBSTRATE_FPH, 1, 0, 0, 0, 0)
        )
        conn.commit()
        cursor.close()
    #
    record_parent(SUBSTRATE_FPH, SUBSTRATE_FPH)
    print("SUBSTRATE_FPH = " + SUBSTRATE_FPH)

    record_private_namespace_root(SUBSTRATE_FPH, "")


def create_seed_entities():

    # (In due course, the default values for the following will be read from a
    # configuration file.)

    # Default values:
    seed_primid_realname        = "Gaia"
    seed_primid_email_1         = "gaia@lrc.org.uk"
    seed_primid_email_2         = ""
    seed_primid_password        = ""    # EDIT
    seed_primid_pin             = ""    # EDIT
    seed_primid_access_token    = ""    # EDIT

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


    # The *substrate* is the nameless *namespace* from which all others ramify,
    # the parent *namespace* of all "root" *namespace* (such as "cc"). This
    # will already have been added to the FPH>HRNS map (at the point of its
    # creation (see fph_hrns_maps.py).
    substrate_hrns = ""

    # NB  There is no need for a seed *secid*

    # First the common proprties entries are created:

    #--------------------------------------------------------------------------
    # Seed *namespace*: "cc"
    #
    # NB  The *namespace* "cc" is a "root" *namespace*. Therefore it has no
    #     named parent *namespace*.

    seed_entity_hrns  = "cc" # The identifier HRNS shared by all seed entities.

    seed_ahid_hrns = seed_currency_hrns = seed_entity_hrns

    print("Registering " + seed_entity_hrns)
    seed_entity_fph = register_identifier(seed_entity_hrns)
    print(seed_entity_fph)

    #record_private_namespace_root(seed_entity_fph, "")


    m = register_entity_type(seed_entity_fph, "primid")

    # Although a *primid* is registered for the seed entity identifier, the
    # corresponding *namespace* is treated as public (an exception)>
    record_private_namespace_root(seed_entity_fph, "")
    if m:
        print(m)
    m = register_entity_type(seed_entity_fph, "ahid")
    if m:
        print(m)
    m = register_entity_type(seed_entity_fph, "namespace")
    if m:
        print(m)
    m = register_entity_type(seed_entity_fph, "currency")
    if m:
        print(m)
    m = register_entity_type(seed_entity_fph, "account")
    if m:
        print(m)
    print("Registered " + seed_entity_hrns)

    seed_namespace_fph = seed_entity_fph
    seed_currency_fph = seed_entity_fph
    seed_primid_fph = seed_entity_fph
    seed_ahid_fph = seed_entity_fph
    seed_account_fph = seed_entity_fph

    pmap = {}
    pmap[seed_ahid_hrns] = {}
    pmap[seed_ahid_hrns][seed_currency_fph] = seed_account_fph
    print("pmap:", end="")
    print(pmap)

    stewards_fph_list = []
    stewards_fph_list.append(seed_primid_fph)
    stewards_fph_blob = pickle.dumps(stewards_fph_list)
    print("stewards_fph_list:", end="")
    print(stewards_fph_list)

    #--------------------------------------------------------------------------
    # Seed *namespace*:

    # The seed *namespace* type-specific properties are added:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO namespaces (" \
                + "entity_fph, " \
                + "active, " \
                + "sandbox, " \
                + "private, " \
                + "stewards_fph_list, " \
                + "default_currency_fph, " \
                + "owner_fph" \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                seed_account_fph,   # *account* FPH
                1,                  # active
                0,                  # sandbox
                0,                  # private
                stewards_fph_blob,  #
                seed_currency_fph,  # *account* *currency*'s FPH'
                seed_ahid_fph       # *account* owner's FPH (*ahid*)
            )
        )
        conn.commit()
        cursor.close()

    #--------------------------------------------------------------------------
    # Seed *account*:

    # The seed *account* type-specific properties are added:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accounts (" \
                + "entity_fph, " \
                + "active, " \
                + "account_owner_fph, " \
                + "account_currency_fph, " \
                + "balance" \
            + ") VALUES (?, ?, ?, ?, ?)",
            (
                seed_account_fph,   # *account* FPH
                1,                  # active
                seed_ahid_fph,      # *account* owner's FPH (*ahid*)
                seed_currency_fph,  # *account* *currency*'s FPH'
                0
            )
        )
        conn.commit()
        cursor.close()

    #--------------------------------------------------------------------------
    # Seed *primid*:

    # Then seed *primid* type-specific properties are added:
    accounts_fph_list = []
    accounts_fph_list.append(seed_account_fph)

    ahids_fph_list = []
    ahids_fph_list.append(seed_ahid_fph)

    nstewardships_fph_list = []
    nstewardships_fph_list.append(seed_namespace_fph)
    cstewardships_fph_list = []
    cstewardships_fph_list.append(seed_currency_fph)

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO primids (" \
                + "entity_fph, " \
                + "active, " \
                + "primid_realname, " \
                + "primid_email_1_hash, " \
                + "primid_email_2_hash, " \
                + "ahids_fph_list, " \
                + "accounts_fph_list, " \
                + "pmap, " \
                + "nstewardships_fph_list, " \
                + "cstewardships_fph_list, " \
                + "password_hash, " \
                + "pin, " \
                + "access_token_hash" \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                seed_primid_fph,
                1,
                seed_primid_realname,
                auth_hash(seed_primid_email_1),
                auth_hash(seed_primid_email_2),
                pickle.dumps([]),
                pickle.dumps(ahids_fph_list),
                pickle.dumps(pmap),
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
                + "active, " \
                + "private, " \
                + "currency_prefix, " \
                + "currency_suffix, " \
                + "default_account_name, " \
                + "stewards_fph_list " \
            + ") VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                seed_currency_fph,
                1,      # active
                0,      # private
                "",     # *currency* prefix
                "",     # *currency* suffix
                "cc",   # default *account* name
                pickle.dumps([seed_primid_fph]) # first steward added to list
            )
        )

    #--------------------------------------------------------------------------
    # The seed *ahid* and *currency* specific properties are added:

        cursor.execute(
            "INSERT INTO ahids (" \
            + "entity_fph, "  \
            + "primid_fph , "  \
            + "accounts_fph_list"  \
            + ") VALUES (?, ?, ?)",
            (
                seed_ahid_fph,
                seed_primid_fph,
                pickle.dumps([seed_account_fph])
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
    seed_primid_fph = nshash("cc")
    seed_currency_fph = nshash("cc")

    errors = "\n"
    tld_fph_list = []
    for tld in cctld_list_here:
        print(tld)
        namespace_fph, namespace_hrns, \
        m = new_namespace(
                tld,
                SUBSTRATE_FPH,
                seed_currency_fph,
                seed_primid_fph
            )
        if m:
            print(m)
        # These root *namespaces* are all public so return no PNSR.
        record_private_namespace_root(namespace_fph, "")
        errors += m + "\n"
        tld_fph_list.append(namespace_fph)

    return tld_fph_list, errors

# A set of single-letter sandbox root *namespaces* is created:
def create_sandbox_root_set():

    # These are recreated here in case it is necessary to call this function
    # before create_seed_entities( ).
    s_fph = register_identifier("s")
    register_entity_type(s_fph, "namespace")

    errors = "\n"
    fph_of = {}
    for s in ["s", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]:
        namespace_fph, namespace_hrns, \
        m = new_namespace(s, s_fph, seed_currency_fph, seed_primid_fph)
        if m:
            print(s + ": ", end="")
            print(m)

        print(namespace_fph + " = " + namespace_hrns)

        fph_of[namespace_hrns] = namespace_fph
        errors += m + "\n"

    return fph_of, errors



#==============================================================================

def create_sandbox_space():

    # The sandbox/demo *namespaces* "sand.box.cc" is created:
    sandox_fph = complete_parent_namespace("sand.box.cc", "cc")
    print("sandox_fph = " + sandox_fph)

    cc_fph, m = hrns_to_fph("cc")
    print("cc_fph = " + cc_fph)

    # Some sandbox/demo *currencies* are created:
    #
    # hrs.box.cc
    currency_fph, currency_hrns, \
    m = new_currency(
            "hrs", sandox_fph, cc_fph, "", "h", "hrs",
            account_type="scalar", category="money", units="unspecified",
            metrical_equivalence="lt", dimensions="unspecified"
        )
    #
    # g£.box.cc
    currency_fph, currency_hrns, \
    m = new_currency(
            "g£", sandox_fph, cc_fph, "£", "", "hrs",
            account_type="scalar", category="money", units="unspecified",
            metrical_equivalence="lt", dimensions="unspecified"
        )
    #
    # cc.sand.box.cc
    currency_fph, currency_hrns, \
    m = new_currency(
            "cc", sandox_fph, cc_fph, "", "", "",
            account_type="scalar", category="money", units="unspecified",
            metrical_equivalence="lt", dimensions="unspecified"
        )

#==============================================================================
