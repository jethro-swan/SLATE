import datetime, time
import xxhash
import json
import math
import os
from base64 import b64encode
import dbm
import sys
from pathlib import Path

from regexp_list import re_fph, re_hrns

from unix_functions import fcopy

from constants import TIMESTAMP_FMT
from constants import FNAME_DATETIME_FMT

#from constants import FPH_TO_HRNS_MAP
#from constants import HRNS_TO_FPH_MAP

#==============================================================================
# 2024-08-18: IMPORTANT
#
# The following functions have been retrieved (and in some cases modified) from
# NESTS. In particular, the FPH<>HRNS mapping functions have been modified from
# the NESTS FPH<>FIP mappings and will be returned to NESTS in order to replace
# the HRNS > FIP > FPH mapping (current in NESTS) with the HRNS > FPH mapping
# used in SLATE.
#
# These changes will simplify compatibility between SLATE and NESTS.
#

#------------------------------------------------------------------------------
# Return Unix timestamp as string:
def unixtime_str():
    return str(time.time_ns()) # nanosecond precision

# Return Unix timestamp as integer:
def unixtime_int():
    return int(time.time_ns()) # nanosecond precision

#------------------------------------------------------------------------------
# Return current date+time in "%Y-%m-%d %H:%M (%A)" format
# YYYY-MM-DD hh:mm (day)
def timestamp():
    return datetime.datetime.now().strftime(TIMESTAMP_FMT)

#------------------------------------------------------------------------------
# Return current date+time in "%Y%m%d%H%M%%S" format
# YYYYMMDDhhmmss
def filename_timestamp():
    return datetime.datetime.now().strftime(FNAME_DATETIME_FMT)

#------------------------------------------------------------------------------
# Map human-readable entity name (UTF-8) to hash:

def nshash(name):
    return xxhash.xxh3_128_hexdigest(name.strip())

def fphash(name):
    return xxhash.xxh3_128_hexdigest(name.strip())


#------------------------------------------------------------------------------

def valid_fph(fph):
    return re_fph.match(fph)

def valid_hrns(hrns):
    return re_hrns.match(hrns)

#------------------------------------------------------------------------------
# Creation and archiving of DBM maps:
#------------------------------------------------------------------------------

# Create new empty map:
def dbm_create_map(dbm_file):
    # map: FPH>HRNS
    with dbm.open(dbm_file, "n", 0o600) as db:
        db.get("")

# Add a key:value pair to the specified DBM file:
def dbm_store(dbm_file, key, value):
    with dbm.open(dbm_file, 'c') as db:
        db[key.encode("utf-8")] = value.encode("utf-8")

# Retrieve a value corresponding to the specified key in the DBM file:
def dbm_fetch(dbm_file, key):
    with dbm.open(dbm_file, 'r') as db:
        k = key.encode("utf-8")
        if k in db:
            value = db[k].decode("utf-8")
        else:
            value = ""
    return value

# Delete a key:value pair from the specified DBM file:
def dbm_delete(dbm_file, key):
    with dbm.open(dbm_file, 'w') as db:
        k = key.encode("utf-8")
        if k in db:
            del db[key.encode("utf-8")]

# List the keys in the specified DBM file:
def dbm_keys(dbm_file):
    key_list = []
    with dbm.open(dbm_file, 'r') as db:
        for k in db.keys():
            key_list.append(k.decode("utf-8"))
    return (key_list)

# List the key:value pairs in the specified DBM file:
def dbm_list_entries(dbm_file):
    with dbm.open(dbm_file, 'r') as db:
        for key in db.keys():
            value = db[k].decode("utf-8")
            print(key + " \t" + value)

#------------------------------------------------------------------------------
# Create new empty FPH<>HRNS maps:
#def create_maps():
#    dbm_create_map(FPH_TO_HRNS_MAP)     # map: FPH>HRNS
#    dbm_create_map(HRNS_TO_FPH_MAP)     # map: HRNS>FPH

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

def hrns_to_fph(hrns):
    # First, the indirect HRNS>FPH map is queried in case this is a known HRNS
    # for which a collision has been identified previously. If the HRNS exists
    # already in the FPH>HRNS map and has been mapped as a collision exception
    # (extremely improbable), its FPH is returned.
    fph = dbm_fetch(HRNS_TO_FPH_MAP, hrns) # (Expecting "")
    if fph: # (exceedingly improbable)
        return fph, ""
    # Otherwise (overwhelmingly probably)
    fph = nshash(hrns)
    hrns_ = fph_to_hrns(fph)
    # If the FPH and HRNS both exist already in the FPH>HRNS map, the FPH is
    # returned unless found to be inconsistent.
    if hrns_:
        if hrns == hrns_:
            return fph, ""
        else:
            return "", "inconsistent FPH"   # This should NEVER happen.
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
        dbm_store(HRNS_TO_FPH_MAP, hrns, fph)
    # In either case, the FPH:HRNS pair is added to the FPH>HRNS map to be used
    # hereafter by fph_to_hrns(fph).
    dbm_store(FPH_TO_HRNS_MAP, fph, hrns)
    return fph

save_fph_to_map = hrns_to_fph # alias

def delete_fph_from_map(fph):
    hrns = dbm_delete(FPH_TO_HRNS_MAP, fph)
    dbm_delete(FPH_TO_HRNS_MAP, fph)
    dbm_delete(HRNS_TO_FPH_MAP, hrns)

#------------------------------------------------------------------------------
