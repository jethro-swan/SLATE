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

import os
import re
from app.core.constants import DB_DIR
from app.core.constants import MAP_BKP_DIR
from app.core.constants import FLAG_MAP
from app.core.constants import CONFIG
from app.core.common import filename_timestamp as timestamp
from app.core.unix_functions import fcopy
from app.core.dbm_functions import dbm_store
from app.core.dbm_functions import dbm_fetch
from app.core.dbm_functions import dbm_delete
from app.core.dbm_functions import dbm_keys
from app.core.dbm_functions import dbm_create_map

#------------------------------------------------------------------------------
# Create new empty flag key:value map

def create_flag_db():
    # If the databases exists already, this is deleted after a time-stamped
    # copy has been saved.
    T = timestamp()
    if os.path.exists(FLAG_MAP):
        os.remove(FLAG_MAP)
    dbm_create_map(FLAG_MAP)
    return

#------------------------------------------------------------------------------
# Retrieve flag value from key key:

def get_flag(flag_key):
    flag_value = dbm_fetch(FLAG_MAP, flag_key).strip()
    if flag_value == "FALSE":
        return False
    elif flag_value == "TRUE":
        return True
    else:
        return False

#------------------------------------------------------------------------------

def delete_flag_key_from_map(flag_key):
    if flag_key is None:
        flag_key = ""
#    flag_value = dbm_delete(FLAG_MAP, flag_key)
    dbm_delete(FLAG_MAP, flag_key)
    return

#------------------------------------------------------------------------------
# Set flag value:

def set_flag(flag_key):
    if isinstance(flag_key, str):
        dbm_store(FLAG_MAP, flag_key, "TRUE")

#------------------------------------------------------------------------------
# Unset flag value:

def unset_flag(flag_key):
    if isinstance(flag_key, str):
        dbm_store(FLAG_MAP, flag_key, "FALSE")
