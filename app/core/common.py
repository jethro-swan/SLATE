import datetime, time
import xxhash
import json
import math
import os
#from base64 import b64encode
#import dbm
import sys
from pathlib import Path

from regexp_list import re_fph, re_hrns

from unix_functions import fcopy

from constants import TIMESTAMP_FMT
from constants import FNAME_DATETIME_FMT


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
