# SLATE
# Last modified: 2024-05-07 14.00 JW

import datetime, time
import xxhash
import json
import math
import os
from base64 import b64encode
import sys
from pathlib import Path

from unix_functions import fcopy
from constants import TIMESTAMP_FMT
from constants import FNAME_DATETIME_FMT

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

#------------------------------------------------------------------------------





#------------------------------------------------------------------------------
# Creation and archiving of DBM maps:

def dbm_store(db_file, key, value):
    with dbm.open(db_file, 'c') as db:
        db[key.encode("utf-8")] = value.encode("utf-8")

def dbm_fetch(db_file, key):
    with dbm.open(db_file, 'r') as db:
        k = key.encode("utf-8")
        if k in db:
            value = db[k].decode("utf-8")
        else:
            value = ""
    return value

def dbm_delete(db_file, key):
    with dbm.open(db_file, 'w') as db:
        k = key.encode("utf-8")
        if k in db:
            del db[key.encode("utf-8")]

def dbm_keys(db_file):
    key_list = []
    with dbm.open(db_file, 'r') as db:
        for k in db.keys():
            key_list.append(k.decode("utf-8"))
    return (key_list)

#------------------------------------------------------------------------------
