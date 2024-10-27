import os

from .unix_functions import fcopy
from .regexp_list import re_fph, re_hrns
from .constants import DB_DIR
from .constants import MAP_BKP_DIR, FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from .common import filename_timestamp as timestamp
from .common import nshash
from .dbm_functions import dbm_store, dbm_fetch, dbm_delete, dbm_keys
from .dbm_functions import dbm_create_map

#------------------------------------------------------------------------------
# Create new empty FPH<>HRNS maps:

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
    # The new empty maps are created:
    #create_maps()
    dbm_create_map(FPH_TO_HRNS_MAP)     # map: FPH>HRNS
    dbm_create_map(HRNS_C_FPH_MAP)     # map: HRNS>FPH

    # These two DBM maps are created initially to ensure that the DB type can
    # be identified correctly by the first read operation.
    null_fph = nshash("")
    ##print("null_fph = " + null_fph)
    dbm_store(FPH_TO_HRNS_MAP, null_fph, "") # FPH>HRNS map
    # The first ("root") entity created (the "global" namespace) has no parent
    # namespace, so a vacuum (an empty string) is used in place of a valid HRNS
    # string. The corresponding FPH must have a valid format.
    dbm_store(HRNS_C_FPH_MAP, "", null_fph) # FPH collision map
    # Although no collision is likely to occur, there is nothing to be lost by
    # creating the reverse mapping in this specific instance.
    return

#------------------------------------------------------------------------------
# Retrieve HRNS from FPH:

def fph_to_hrns(fph):
    if re_fph.match(fph):
        hrns = dbm_fetch(FPH_TO_HRNS_MAP, fph)
        return hrns
    else:
        return ""

fph_exists = fph_to_hrns # function alias

# Most frequently (e.g. when mapping a known HRNS to its FPH), this function
# will not add anything to the FPH>HRNS map. Only when an unknown HRNS is
# passed will the FPH>HRNS map be affected.

def hrns_to_fph(hrns): # returns FPH and message
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
        dbm_store(HRNS_C_FPH_MAP, hrns, fph)
    # In either case, the FPH:HRNS pair is added to the FPH>HRNS map to be used
    # hereafter by fph_to_hrns(fph).
    dbm_store(FPH_TO_HRNS_MAP, fph, hrns)
    return fph, ""

save_fph_to_map = hrns_to_fph # alias

#------------------------------------------------------------------------------

def delete_fph_from_map(fph):
    hrns = dbm_delete(FPH_TO_HRNS_MAP, fph)
    dbm_delete(FPH_TO_HRNS_MAP, fph)
    dbm_delete(HRNS_C_FPH_MAP, hrns)

#------------------------------------------------------------------------------



#==============================================================================
# When any entity is moved to a new namespace, the HRNS>FPH and FPH>HRNS
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
