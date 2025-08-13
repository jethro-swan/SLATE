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

from app.core.messaging import send_message

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from app.core.fph_hrns_maps import delete_fph_from_map

from app.core.dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from app.core.dbm_functions import dbm_create_map

from app.core.auth import auth_hash, check_auth_hash, generate_access_token

from app.core.regexp_list import *

from app.core.unix_functions import fcopy

from app.core.cctld_list import *


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
        print(m)
        print("Deleting " + identifier_fph + " from map")
        delete_fph_from_map(identifier_fph)
        return ""

    print("identifier_fph = " + identifier_fph)

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

    print("-"*160)
    id_fph,  id_hrns, etypes, m = identify_entity(identifier_fph)
    print("New identifier registered: " + identifier_fph)
    print("id_fph = " + id_fph)
    print("id_hrns = " + id_hrns)
    print("etypes = ", end="")
    print(etypes)
    print("-"*160)

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
    print("identifier_hrns 2 = " + identifier_hrns)
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
    print("(1) entity_id = " + entity_id)
    if entity_id == SUBSTRATE_FPH: # unique exception
        #print("substrate")
        return entity_id, "", list("namespace",), ""
    if re_fph.match(entity_id): # this is an FPH string?
        print(entity_id + " is an FPH")
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
        print(entity_id + " is an HRNS")
        entity_hrns = entity_id
        entity_fph, m = hrns_to_fph(entity_id)
        if m: # something wrong here
            print("something wrong here")
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
    print("split: " + name + " & ", end="")
    print(names)
    parent_hrns = NSS.join(names).strip(NSS)
    print(">>> " + name + ":" + parent_hrns)
    return name, parent_hrns


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

def is_in_private_namespace(entity_hrns, pn_id):
    pn_fph, pn_hrns, etype, m = identify_entity(pn_id)
    return is_ancestor(entity_hrns, pn_hrns) or (entity_hrns == pn_hrns)



#=============================================================================

def retrieve_pmap(owner_id):
    owner_fph, owner_hrns, etypes, m = identify_entity(owner_id)
    if not owner_fph:
        print("retrieve_pmap: " + owner_fph + " is not registered")
        return {}, owner_id + " is not registered"
    if not ("primid" in etypes):
        print("retrieve_pmap: " + owner_id + " is not a primid")
        return {}, owner_id + " is not a primid"
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
        print("retrieve_pmap: no pmap for " + owner_hrns + " (a)")
        return {}, ""
    #elif isinstance(result, tuple) and (result[0] is None):
    elif result[0] is None:
        print("retrieve_pmap: no pmap for " + owner_hrns + " (b)")
        return {}, ""
    else:
        pmap = pickle.loads(result[0])
        print("retrieve_pmap: pmap for " + owner_hrns + " :")
        print(pmap)
        return pmap, ""     # dictionary of  ahid_hrns:currency_hrns
                            # pairs for display in table.

#=============================================================================

def new_pairing(
        owner_id,       # *primid* HRNS or FPH
        ahid_hrns,      # *ahid* HRNS (may not exist yet)
        currency_id     # *currency* HRNS or FPH (must exist already)
    ):
    # The *currency* and owner *primid* are validated before proceeding to
    # create a new *ahid* (*account-holder identity*. Only if both exist will a
    # new *account* or *ahid* be created.
    currency_fph, currency_hrns, cetypes, m = identify_entity(currency_id)
    if m:
        print("identify_entity(currency_id): " + m)
    if not currency_fph:
        print(currency_id + " is not a registered identifier (12)")
        return "", currency_id + " is not a registered identifier (12)"
    if not ("currency" in cetypes):
        print(currency_hrns + " is not a currency")
        return "", currency_hrns + " is not a currency"
    owner_fph, owner_hrns, petypes, m = identify_entity(owner_id)
    if m:
        print("identify_entity(owner_id)" + m)
    if not owner_fph:
        print(owner_id + " is not a registered identifier (13)")
        return "", "", owner_id + " is not a registered identifier (13)"
    if not ("primid" in petypes):
        print(owner_hrns + " is not a primid")
        return "", "", owner_hrns + " is not a primid"
    print("meow!")
    # If the *ahid* does not exist already it must be created:
    print("ahid_hrns supplied = " + ahid_hrns)
    r_ahid_fph, r_ahid_hrns, etypes, m = identify_entity(ahid_hrns)
    print("ahid_hrns retrieved = " + r_ahid_hrns)
    if not ("ahid" in etypes):
        # A new *ahid* is created:
        ahid_name, parent_hrns = split_hrns(ahid_hrns)
        print("ahid_hrns = " + ahid_hrns)
        print("ahid_name = " + ahid_name)
        ahid_fph, ahid_hrns, m = new_ahid(ahid_name, parent_hrns, owner_fph)
        print("Creating ahid " + ahid_hrns)
    else:
        ahid_fph = r_ahid_fph
        ahid_hrns = r_ahid_hrns
    print("ahid_hrns = " + ahid_hrns)
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
    print("pairing account name = " + account_name)
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
            currency_fph
        )
    print("woof!")

    print("new_pairing: account = " + account_fph + " > " + account_hrns)

    print("Zeppo")

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
        if not (ahid_fph in ahids_fph_list):
            ahids_fph_list.append(ahid_fph)
            cursor.execute(
                "UPDATE primids SET ahids_fph_list = ? WHERE entity_fph = ?",
                (pickle.dumps(ahids_fph_list), owner_fph)
            )
            conn.commit()
        cursor.close()
    return account_fph, account_hrns, ""

#=============================================================================
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
