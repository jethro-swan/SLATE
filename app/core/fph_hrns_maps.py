import os
import sqlite3

from app.core.unix_functions import fcopy
from app.core.regexp_list import re_fph, re_hrns
from app.core.constants import DB_DIR
from app.core.constants import MAP_BKP_DIR
from app.core.constants import FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from app.core.constants import FPH_PARENT_MAP
from app.core.constants import FPH_HRNS_MAP
from app.core.constants import MAP_DB

from app.core.constants import PNSR_MAP
from app.core.constants import SUBSTRATE_FPH
from app.core.common import filename_timestamp as timestamp
from app.core.common import nshash
from app.core.dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from app.core.dbm_functions import dbm_create_map


# 2025-08-30: Extended to add a mapping of any identifier to its parent in
# order to simplify the separation of private *namespaces* from those anchored
# in *namespaces* ramifying from the root. This avoids the need to perform a
# chain of SQLite database queries.
#
# In due course, this may be used to remove the need for a parent FPH field in
# the entities tables. Alternatively, it may be useful to keep both in place in
# order to simplify consistency checks.

# 2025-09-06: PNSR_MAP added - private namespace root
# The identifier of each entity is anchored within a *namespace* (sub)tree,
# whether in the "public" default namespace or within the private *namespace*
# tree belonging to a *primid*.
# Entities within a private *namespace* tree are stored within a pair of SQLite
# databases identified by the FPH of that subtree's root, e.g.
#   entities_250dbf0cad6b75c3a40d42dacd66cba0.db
#   payments_250dbf0cad6b75c3a40d42dacd66cba0.db
# whereas those in the public spaces are saved in
#   entities.db
#   payments.db


# 2025-10-08: Moving FPH<>HRNS mapping from DBM to SQLite3


#------------------------------------------------------------------------------
# Create new empty FPH<>HRNS and entity>parent (FPH>FPH) maps:

# 2025-10-08: A collection of DBM maps is replace by a single SQLite3 database.
# Replace create_maps() with create_map() later.

def create_maps(): # SQLite
    # If the databases exists already, they are deleted. (A time-stamped
    # copy will have been saved by ~/initialize.py.)
    T = timestamp()
    if os.path.exists(MAP_DB):
        os.remove(MAP_DB)
    # create or open DB (this creates the file if it doesn't exist)
    conn = sqlite3.connect(MAP_DB)
    conn.execute("PRAGMA user_version;")
    conn.close()
    # set permissions to 660 (rw-rw----)
    os.chmod(MAP_DB, 0o660)

    substrate_fph = nshash("")

    with sqlite3.connect(MAP_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS fph_hrns_map (" \
            + "fph TEXT PRIMARY KEY NOT NULL, " \
            + "hrns TEXT DEFAULT ''" \
            + ");"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS hrns_fph_map (" \
            + "hrns TEXT PRIMARY KEY NOT NULL, " \
            + "fph TEXT DEFAULT ''" \
            + ");"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS hrns_c_fph_map (" \
            + "hrns TEXT PRIMARY KEY NOT NULL, " \
            + "fph TEXT DEFAULT ''" \
            + ");"
        )
        conn.commit()
        cursor.close()

    return


#------------------------------------------------------------------------------
# Retrieve HRNS from FPH:

def fph_to_hrns(fph):
    if not re_fph.match(fph):
        return ""
    with sqlite3.connect(MAP_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT hrns FROM fph_hrns_map WHERE fph = ?", (fph,))
        result = cursor.fetchone()
    if (result is None) or (result[0] is None):
        #return ""
        hrns = ""
    else:
        #return result[0]
        hrns = result[0]
#    print("fph_to_hrns: " + fph + " > " + hrns)
    return hrns

fph_exists = fph_to_hrns # function alias

#def hrns_exists_already(hrns):
#    fph = nshash(hrns)
#    return (fph_to_hrns(fph) == hrns)

def hrns_exists_already(hrns):
    with sqlite3.connect(MAP_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT fph FROM hrns_fph_map WHERE hrns = ?",
            (hrns,)
        )
        result = cursor.fetchone()
        if result is not None:
            return True
        else:
            return False




def hrns_to_fph(hrns): # returns FPH and message
    if hrns == "":
        return SUBSTRATE_FPH, ""
    elif not re_hrns.match(hrns):
        return "", "Invalid HRNS"
    # Most frequently (when mapping a known HRNS to its FPH), this function
    # will not add anything to the HRNS>FPH and FPH>HRNS map. Only when an
    # unknown HRNS is passed will the map be extended.
    with sqlite3.connect(MAP_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT fph FROM hrns_fph_map WHERE hrns = ?", (hrns,))
        result = cursor.fetchone()
        if (result is not None) and (result[0] != ""):
            cursor.close()
            return result[0], "" # known FPH returned
        else:
            # In the vast majority of cases, the FPH will be a simple hash of
            # the HRNS.
            fph = nshash(hrns)
            # If the FPH is already in the FPH>HRNS map, it will be rehashed
            # repeatedly until no collision is found. (Although this will be an
            # exceedingly rare event, it will not be impossible.)
#            tcount = 0 # TESTSTUFF
            while fph_to_hrns(fph):
#                tcount += 1 # TESTSTUFF
                fph = nshash(fph)
#            if tcount > 0: # TESTSTUFF
#                print("Rehash required: " + str(tcount)) # TESTSTUFF
            cursor.execute(
                "INSERT INTO fph_hrns_map (fph, hrns) VALUES (?, ?)",
                (fph, hrns)
            )
            cursor.execute(
                "INSERT INTO hrns_fph_map (hrns, fph) VALUES (?, ?)",
                (hrns, fph)
            )
            conn.commit()
            cursor.close()
            return fph, ""


save_fph_to_map = hrns_to_fph # alias

#------------------------------------------------------------------------------

def delete_fph_from_map(fph):
    if not re_fph.match(fph):
        return "Invalid FPH"
    with sqlite3.connect(MAP_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM fph_hrns_map WHERE fph = ?",
            (fph,)
        )
        result = cursor.fetchone()
        if (result is None) or (result[0] is None):
            return "FPH not registered"
        else:
            cursor.execute(
                "DELETE FROM fph_hrns_map WHERE fph = ?",
                (fph,)
            )
            conn.commit()
        cursor.close()
    return ""

#------------------------------------------------------------------------------


#==============================================================================
# A note on PRUNING & GRAFTING  (2025-11-10)
#
# Inserting one or more *namespaces* into a path involves
# (1) creation of a new branch at the insertion point, and
# (2) movement of the chain of descendant *namespaces* chain to the end of the
#     newly-created branch.
# e.g.
# inserting  p.q.r  into  a.b.c.d.e  between  a.b  and  c.d.e  would involve
# creation of *namespace* chain  p.q.r.c.d.e  and the movement of  b  (along
# with all of its descendants) from *namespace*  c.d.e  into *namespace*
# p.q.r.c.d.e  to form the new *namespace* chain  a.b.p.q.r.c.d.e
#
# Such an action requires authorization both from the stewards of  c.d.e  and
# from the stewards of  b  at the very least, and will probably be a rather
# infrequent event. In most cases it would be reasonable to require the consent
# of the stewards of all the descendant namespaces of  b  and this additional
# inconvenience is likely to make it an even more unusual event.
#
# Similarly, the removal of a *namespace* chain would require (at the very
# least) the approval of the stewards of all entities within that chain.
# Furthermore, the disruption arising from a change of HRNS suggests that all
# such operations should be undertaken only in exceptional circumstances. In
# general, it will be far better to predict the required ramifications and to
# create chains of (initially empty) *namespaces* than to make ad hoc changes.
#
# For this reason, creation of functions to perform pruning and grafting may
# be too low a priority justify the robust versions required for use within
# open *namespaces*. However, slightly simpler versions (omitting the strict
# multi-/omni-steward authorization requirements) may be very useful in private
# *namespaces*, especially to help in planning the structure of such trees for
# construction (replication) within open *namespace* trees.

#------------------------------------------------------------------------------
# An additional note regarding FPH and HRNS
#
# For any entity, the only identifier guaranteed to be invariant is its FPH.
# The HRNS may change (but such changes should probablbe avoided as far as
# possible).
#
#------------------------------------------------------------------------------



#==============================================================================
# When any entity is moved to a new *namespace*, the HRNS>FPH and FPH>HRNS
# mappings must be updated.

def update_mapping(current_hrns, new_hrns):

    if not re_hrns.match(current_hrns):
        return current_hrns + " is not a valid HRNS"
    if not re_hrns.match(new_hrns):
        return current_hrns + " is not a valid HRNS"

    # The FPH (originally assigned as hash of HRNS) must be preserved:
    current_fph, m = hrns_to_fph(current_hrns)
    if not current_fph:
        return "HRNS " + current_hrns + " has not been registered"
    if m:
        return m # error message

    if current_hrns == new_hrns:
        return ""

    # The entity's HRNS is updated but its FPH must remain the same. Therefore,
    # whereas the original FPH is a simple hash of the HRNS when first mapped,
    # any subsequent update to the HRNS must be mapped to the original FPH (and
    # vice versa).
    #
    with sqlite3.connect(MAP_DB) as conn:
        cursor = conn.cursor()
        # (1) The HRNS>FPH map must be updated
        #
        cursor.execute(
            "INSERT INTO hrns_fph_map (hrns, fph) VALUES (?, ?)",
            (new_hrns, current_fph)
        )
        cursor.execute(
            "DELETE FROM hrns_fph_map WHERE hrns = ?",
            (current_hrns,)
        )
        # (2) The FPH>HRNS map must be updated
        # 2.1 The FPH>HRNS mapping must be deleted first because FPH is unique.
        cursor.execute(
            "DELETE FROM fph_hrns_map WHERE fph = ?",
            (current_fph,)
        )
        # 2.2 The new FPH>HRNS mapping can now be inserted.
        cursor.execute(
            "INSERT INTO fph_hrns_map (fph, hrns) VALUES (?, ?)",
            (current_fph, new_hrns)
        )
        conn.commit()
        cursor.close()
    return ""

#==============================================================================
# Move *namespace* ns1 (and its contents) into *namespace* ns2.
# e.g.
# moving b.c.d.e into f.g.h changes
#   a.b.c.d.e
# to
#   a.b.f.g.h

# NB: The function defined below is still incomplete. Each individual HRNS
# within the tree of descendants must also be updated.
#
# New functions needed:
#   list_children(namespace_id)     return list of FPH (all entity types)
#   list_descendants(namespace_id)  return list of FPH (all entity types)
#
# The former can probably be built by listing all identifiers sharing a
# specified parent. The latter can probably be built by apply the former
# repeatedly.

def move_namespace(ns1_id, ns2_id):

    ns1_fph, ns1_hrns, etypes, m = identify_entity(ns1_id)
    if not ns1_fph:
        return "", "", ns1_id + " is not a registered identifier"
    if not ("namespace" in etypes):
        return "", "", ns1_hrns + " is not a registered namespace identifier"

    ns2_fph, ns2_hrns, etypes, m = identify_entity(ns2_id)
    if not ns2_fph:
        return "", "", ns2_id + " is not a registered identifier"
    if not ("namespace" in etypes):
        return "", "", ns2_hrns + " is not a registered namespace identifier"

    ns1_name, ns1_parent = split_hrns(ns1_hrns)
    ns3_hrns = ns1_name + "." + ns2
    ns3_fph, ns3_hrns, etypes, m = identify_entity(ns3_hrns)
    if ns3_fph and ("namespace" in etypes):
        return "", "", "Namespace " + ns3_fph + " exists already"

    m = update_mapping(ns1_hrns, ns3_hrns)
    if m:
        return "", "", m
    # The new mapping is verified:
    ns3_fph, ns3_hrns, etypes, m = identify_entity(ns3_hrns)
    if ns3_fph:
        return ns3_fph, ns3_hrns, ""
    else:
        return "", "", m
