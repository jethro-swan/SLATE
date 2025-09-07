import os

from app.core.unix_functions import fcopy
from app.core.regexp_list import re_fph, re_hrns
from app.core.constants import DB_DIR
from app.core.constants import MAP_BKP_DIR, FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from app.core.constants import FPH_PARENT_MAP
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



#------------------------------------------------------------------------------
# Create new empty FPH<>HRNS and entity>parent (FPH>FPH) maps:

def create_maps(): # MDB map
    # If the databases exists already, they are deleted after a time-stamped
    # copy has been saved.
    T = timestamp()
    ##print(T)
    if os.path.exists(FPH_TO_HRNS_MAP):
        fcopy(FPH_TO_HRNS_MAP, MAP_BKP_DIR + 'FPH_TO_HRNS_MAP_' + T + '.dbm')
        os.remove(FPH_TO_HRNS_MAP)
    if os.path.exists(HRNS_C_FPH_MAP):
        fcopy(HRNS_C_FPH_MAP, MAP_BKP_DIR + 'HRNS_C_FPH_MAP_' + T + '.dbm')
        os.remove(HRNS_C_FPH_MAP)
    # Added 2025-08-30:
    if os.path.exists(FPH_PARENT_MAP):
        fcopy(FPH_PARENT_MAP, MAP_BKP_DIR + 'FPH_PARENT_MAP_' + T + '.dbm')
        os.remove(FPH_PARENT_MAP)
    # Added 2025-09-06:
    if os.path.exists():
        fcopy(PNSR_MAP, MAP_BKP_DIR + 'PNSR_MAP_' + T + '.dbm')
        os.remove(PNSR_MAP)
    # The new empty maps are created:
    #create_maps()
    dbm_create_map(FPH_TO_HRNS_MAP)     # map: FPH>HRNS
    dbm_create_map(HRNS_C_FPH_MAP)      # map: HRNS>FPH
    # Added 2025-08-30:
    dbm_create_map(FPH_PARENT_MAP)      # map: FPH>FPH (child>parent)
    # Added 2025-09-06:
    dbm_create_map(PNSR_MAP)
    # These two DBM maps are created initially to ensure that the DB type can
    # be identified correctly by the first read operation.
    substrate_fph = nshash("")
    ##print("substrate_fph = " + substrate_fph)
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

def fph_to_hrns(fph):
    if re_fph.match(fph):
        hrns = dbm_fetch(FPH_TO_HRNS_MAP, fph).strip()
        return hrns
    else:
        return ""

fph_exists = fph_to_hrns # function alias

def hrns_exists_already(hrns):
    fph = nshash(hrns)
    return (fph_to_hrns(fph) == hrns)

# Most frequently (e.g. when mapping a known HRNS to its FPH), this function
# will not add anything to the FPH>HRNS map. Only when an unknown HRNS is
# passed will the FPH>HRNS map be affected.

def hrns_to_fph(hrns): # returns FPH and message

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

save_fph_to_map = hrns_to_fph # alias

#------------------------------------------------------------------------------

def delete_fph_from_map(fph):

    if fph is None: ## 2025-01-212
        fph = ""

    hrns = dbm_delete(FPH_TO_HRNS_MAP, fph)
    dbm_delete(FPH_TO_HRNS_MAP, fph)
    dbm_delete(HRNS_C_FPH_MAP, hrns)

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

def record_parent(entity_fph, parent_fph):
    return dbm_store(FPH_PARENT_MAP, entity_fph, parent_fph)

# Retrieve parent FPH from any entity FPH:

def get_parent(entity_fph):
    if re_fph.match(entity_fph):
        parent_fph = dbm_fetch(FPH_PARENT_MAP, entity_fph).strip()
        return parent_fph
    else:
        return ""

#------------------------------------------------------------------------------
# Record private "namespace* root FPH:

def record_private_namespace_root(entity_fph, private_namespace_root_fph):
    # Return True iff stored successfully:
    return dbm_store(PNSR_MAP, entity_fph, private_namespace_root_fph)

# Retrieve private "namespace* root FPH:

def get_private_namespace_root(entity_fph):
    if re_fph.match(entity_fph):
        private_namespace_root_fph = dbm_fetch(PNSR_MAP, entity_fph).strip()
        return private_namespace_root_fph
    else:
        return ""
