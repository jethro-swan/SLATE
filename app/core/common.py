# NESTS/SLATE - a networked tool to support user-created and -stewarded
# currencies and measures (open money and open measure)
# Copyright (C) 2026. 2025, 2024, 2023, 2022 John Waters
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime, time
import xxhash
import json
import math
import os
#from base64 import b64encode
#import dbm
import sys
from pathlib import Path

from app.core.regexp_list import re_fph, re_hrns

from app.core.unix_functions import fcopy

from app.core.constants import TIMESTAMP_FMT, FNAME_DATETIME_FMT
from app.core.constants import LEDGER_DATETIME_FMT

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
# Return current date+time in "%Y-%m-%d_%H%M%%S" format
# YYYYMMDDhhmmss
def filename_timestamp():
    return datetime.datetime.now().strftime(FNAME_DATETIME_FMT)

#------------------------------------------------------------------------------
# Return current date+time in "%Y-%m-%d %H:%M:%S" format
# YYYY-MM-DD hh:mm:ss:ms
def ledger_timestamp():
    return datetime.datetime.now().strftime(LEDGER_DATETIME_FMT)


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
