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

def __hrns_to_fph(hrns): # returns FPH and message
    if hrns == "":
        return SUBSTRATE_FPH, ""
    fph = dbm_fetch(HRNS_C_FPH_MAP, hrns) # (Expecting "")
    if fph: # (exceedingly improbable)
        return fph, ""


    fph = nshash(hrns)
    hrns_ = fph_to_hrns(fph)
    if hrns_:
        if hrns == hrns_:
            return fph, ""
        else:
            return "", "inconsistent FPH>HRNS mapping" # should NEVER happen.
    else:
        while fph_to_hrns(fph):
            fph = nshash(fph)
        while not dbm_store(HRNS_C_FPH_MAP, hrns, fph):
            continue
    while not dbm_store(FPH_TO_HRNS_MAP, fph, hrns):
        continue

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
# When any entity is moved to a new *namespace*, the HRNS>FPH and FPH>HRNS
# mappings must be updated.

def update_mapping(current_hrns, new_hrns):

    if not re_hrns.match(current_hrns):
        return current_hrns + " is not a valid HRNS", ""

    current_fph, m = hrns_to_fph(current_hrns)
    if not current_fph:
        return "HRNS " + current_hrns + " has not been registered"
    if m:
        return m # error message

    # The entity's HRNS is updated but its FPH must remain the same. Therefore,
    # whereas the original FPH is a simple hash of the HRNS when first mapped,
    # any subsequent update to the HRNS must be mapped to the original FPH (and
    # vice versa).
    #
    # (1) HRNS>FPH map must be updated
    #dbm_delete(HRNS_C_FPH_MAP, current_hrns)
    dbm_store(HRNS_C_FPH_MAP, new_hrns, current_fph)

    # (2) FPH>HRNS map must be updated
    #dbm_delete(FPH_TO_HRNS_MAP, current_fph)
    dbm_store(FPH_TO_HRNS_MAP, current_fph, new_hrns)

    return ""

#==============================================================================
##
# Added 2025-08-30:

#------------------------------------------------------------------------------
# Record parent FPH:

#def record_parent(id_fph, parent_fph):
#    return dbm_store(FPH_PARENT_MAP, id_fph, parent_fph)

# Retrieve parent FPH from any entity FPH:

#def get_parent(id_fph):
#    if re_fph.match(id_fph):
#        parent_fph = dbm_fetch(FPH_PARENT_MAP, id_fph).strip()
#        return parent_fph
#    else:
#        return ""

#------------------------------------------------------------------------------
# Record private "namespace* root FPH:

#def record_private_namespace_root(id_fph, private_namespace_root_fph):
#    # Return True iff stored successfully:
#    return dbm_store(PNSR_MAP, id_fph, private_namespace_root_fph)

# Retrieve private "namespace* root FPH:

#def get_private_namespace_root(id_fph):
#    if re_fph.match(id_fph):
#        private_namespace_root_fph = dbm_fetch(PNSR_MAP, id_fph).strip()
#        return private_namespace_root_fph
#    else:
#        return ""





###############################################################################

def _create_maps(): # DBM map
    # If the databases exists already, they are deleted after a time-stamped
    # copy has been saved.
    T = timestamp()
    if os.path.exists(FPH_TO_HRNS_MAP):
        os.remove(FPH_TO_HRNS_MAP)
    if os.path.exists(HRNS_C_FPH_MAP):
        os.remove(HRNS_C_FPH_MAP)
    if os.path.exists(FPH_PARENT_MAP):
        os.remove(FPH_PARENT_MAP)
    if os.path.exists(PNSR_MAP):
        os.remove(PNSR_MAP)
    # The new empty maps are created:
    dbm_create_map(FPH_TO_HRNS_MAP)     # map: FPH>HRNS
    dbm_create_map(HRNS_C_FPH_MAP)      # map: HRNS>FPH
    dbm_create_map(FPH_PARENT_MAP)      # map: FPH>FPH (child>parent)
    dbm_create_map(PNSR_MAP)
    # These two DBM maps are created initially to ensure that the DB type can
    # be identified correctly by the first read operation.
    substrate_fph = nshash("")
    dbm_store(FPH_TO_HRNS_MAP, substrate_fph, "") # FPH>HRNS map
    # The first "root" entity created (the "cc" namespace) has no named parent
    # namespace, its parent namespace being the nameless "substrate". Although
    # this contains no names, and is therefore not a *namespace*, it does have
    # some of the properties of such. In particular, it must have a valid FPH
    # corresponding to an empty string.
    dbm_store(HRNS_C_FPH_MAP, "", substrate_fph) # FPH collision map
    # Although no collision is likely to occur, there is nothing to be lost by
    # creating the reverse mapping in this specific instance.
    return

#------------------------------------------------------------------------------
# Retrieve HRNS from FPH:

def _fph_to_hrns(fph):
    if re_fph.match(fph):
        hrns = dbm_fetch(FPH_TO_HRNS_MAP, fph).strip()
        return hrns
    else:
        return ""

fph_exists = fph_to_hrns # function alias

def _hrns_exists_already(hrns):
    fph = nshash(hrns)
    return (fph_to_hrns(fph) == hrns)

# Most frequently (e.g. when mapping a known HRNS to its FPH), this function
# will not add anything to the FPH>HRNS map. Only when an unknown HRNS is
# passed will the FPH>HRNS map be affected.

def _hrns_to_fph(hrns): # returns FPH and message

    if hrns == "":
        return SUBSTRATE_FPH, ""

    # First, the indirect HRNS>FPH map is queried in case this is a known HRNS
    # for which a collision has been identified previously. If the HRNS exists
    # already in the HRNS>FPH collisions map and has been mapped as a collision
    # exception (extremely improbable), its FPH is returned.
    fph = dbm_fetch(HRNS_C_FPH_MAP, hrns) # (Expecting "")
    if fph: # (exceedingly improbable)
        return fph, ""

    # If the HRNS is not listed in the collision map (overwhelmingly probably)
    # a provional FPH is hashed:
    fph = nshash(hrns)
    hrns_ = fph_to_hrns(fph)
    # If the FPH and HRNS both exist already in the FPH>HRNS map, the FPH is
    # returned unless found to be inconsistent.
    if hrns_:
        if hrns == hrns_:
            #print(">>> HRNS mapping collision")
            return fph, ""
        else:
            return "", "inconsistent FPH>HRNS mapping" # should NEVER happen.

    # On the other hand, if the HRNS is not yet known (in the FPH>HRNS map):
    else:
        # At this point, the FPH hashed above from the HRNS will usually be
        # unique (so not already in the FPH>HRNS map), but collisions are not
        # impossible. In the rare case of a collision, a new FPH must be found
        # (in this case by repeatedly hashing the FPH itself).
        while fph_to_hrns(fph):
            fph = nshash(fph)
        # The collision-causing HRNS is now added to the FPH in the HRNS>FPH
        # exception map (which will usually be empty and will never grow beyond
        # a very small size) to be queried hereafter by hrns_to_fph(hrns).
##        dbm_store(HRNS_C_FPH_MAP, hrns, fph)
# 2025-03-01: experimental change
        while not dbm_store(HRNS_C_FPH_MAP, hrns, fph):
            continue
    # In either case, the FPH:HRNS pair is added to the FPH>HRNS map to be used
    # hereafter by fph_to_hrns(fph).
##    dbm_store(FPH_TO_HRNS_MAP, fph, hrns)
# 2025-03-01: experimental change
    while not dbm_store(FPH_TO_HRNS_MAP, fph, hrns):
        continue

    return fph, ""

#save_fph_to_map = hrns_to_fph # alias

#------------------------------------------------------------------------------

def _delete_fph_from_map(fph):

    if fph is None: ## 2025-01-212
        fph = ""

    hrns = dbm_delete(FPH_TO_HRNS_MAP, fph)
    dbm_delete(FPH_TO_HRNS_MAP, fph)
    dbm_delete(HRNS_C_FPH_MAP, hrns)

#------------------------------------------------------------------------------



#==============================================================================
# When any entity is moved to a new *namespace*, the HRNS>FPH and FPH>HRNS
# mappings must be updated.

def _update_mapping(current_hrns, new_hrns):

    if not re_hrns.match(current_hrns):
        return current_hrns + " is not a valid HRNS", ""

    current_fph, m = hrns_to_fph(current_hrns)
    if not current_fph:
        return "HRNS " + current_hrns + " has not been registered"
    if m:
        return m # error message

    # The entity's HRNS is updated but its FPH must remain the same. Therefore,
    # whereas the original FPH is a simple hash of the HRNS when first mapped,
    # any subsequent update to the HRNS must be mapped to the original FPH (and
    # vice versa).
    #
    # (1) HRNS>FPH map must be updated
    #dbm_delete(HRNS_C_FPH_MAP, current_hrns)
    dbm_store(HRNS_C_FPH_MAP, new_hrns, current_fph)

    # (2) FPH>HRNS map must be updated
    #dbm_delete(FPH_TO_HRNS_MAP, current_fph)
    dbm_store(FPH_TO_HRNS_MAP, current_fph, new_hrns)

    return ""

#==============================================================================
##
# Added 2025-08-30:

#------------------------------------------------------------------------------
# Record parent FPH:

def _record_parent(id_fph, parent_fph):
    return dbm_store(FPH_PARENT_MAP, id_fph, parent_fph)

# Retrieve parent FPH from any entity FPH:

def _get_parent(id_fph):
    if re_fph.match(id_fph):
        parent_fph = dbm_fetch(FPH_PARENT_MAP, id_fph).strip()
        return parent_fph
    else:
        return ""

#------------------------------------------------------------------------------
# Record private "namespace* root FPH:

def _record_private_namespace_root(id_fph, private_namespace_root_fph):
    # Return True iff stored successfully:
    return dbm_store(PNSR_MAP, id_fph, private_namespace_root_fph)

# Retrieve private "namespace* root FPH:

def _get_private_namespace_root(id_fph):
    if re_fph.match(id_fph):
        private_namespace_root_fph = dbm_fetch(PNSR_MAP, id_fph).strip()
        return private_namespace_root_fph
    else:
        return ""
