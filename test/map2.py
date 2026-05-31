#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import random
import os
import pickle
from pathlib import Path
from string import ascii_lowercase

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



NSS = "."

M2DB_PATH = "/var/slate/active/test/map2"

hrns_a = "abc.def.ghi.jkl.mno.prq"

hrns_path_list = hrns_a.split(NSS)

print(hrns_path_list)


# Create a new map (SQLite)

def new_map(root_fph):

    MAP_DB = M2DB_PATH + "/" + root_fph + "_map"
    print("MAP_DB = " + MAP_DB)

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

#    substrate_fph = nshash("")

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


def root_map():

    new_map(SUBSTRATE_FPH)


#------------------------------------------------------------------------------





def hrns_to_fph(name, parent_fph): # returns FPH and message
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
            while fph_to_hrns(fph):
                fph = nshash(fph)
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
        hrns = ""
    else:
        hrns = result[0]
    return hrns
