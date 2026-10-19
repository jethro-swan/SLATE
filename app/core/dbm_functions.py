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

import dbm
from base64 import b64encode

#------------------------------------------------------------------------------
# Creation and archiving of DBM maps:
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Create new empty map:
def dbm_create_map(dbm_file):
    #with dbm.open(dbm_file, "n", 0o600) as db:
    with dbm.open(dbm_file, "n", 0o660) as db:
    #with dbm.sqlite3.open(dbm_file, /, "n", 0o600) as db:
        db.get("")



#------------------------------------------------------------------------------
# Add a key:value pair to the specified DBM file:
def dbm_store(dbm_file, key, value):

    # Original version:
#    with dbm.open(dbm_file, 'c') as db:
#        db[key.encode("utf-8")] = value.encode("utf-8")

# 2025-03-01: experimental change
    try:
        db = dbm.open(dbm_file, 'c')
    except:
        db.close()
        return False
    finally:
        db[key.encode("utf-8")] = value.encode("utf-8")
        db.close()
        return True

#------------------------------------------------------------------------------
# Retrieve a value corresponding to the specified key in the DBM file:
def dbm_fetch(dbm_file, key):

    # Original version:
    with dbm.open(dbm_file, 'r') as db:
        k = key.encode("utf-8")
        if k in db:
            value = db[k].decode("utf-8")
        else:
            value = ""
    return value

#------------------------------------------------------------------------------
# Delete a key:value pair from the specified DBM file:
def dbm_delete(dbm_file, key):
    if key is None:
        return
    with dbm.open(dbm_file, 'w') as db:
        k = key.encode("utf-8")
        if k in db:
            del db[key.encode("utf-8")]
    return

# List the keys in the specified DBM file:
def dbm_keys(dbm_file):
    key_list = []
    with dbm.open(dbm_file, 'r') as db:
        for k in db.keys():
            key_list.append(k.decode("utf-8"))
    return (key_list)

# List the key:value pairs in the specified DBM file:
def dbm_list_entries(dbm_file):
    dbm_entries = {}
    with dbm.open(dbm_file, 'r') as db:
        for k in db.keys():
            key = k.decode("utf-8")
            value = db[k].decode("utf-8")
            dbm_entries[key] = value
            #print(key + " \t" + value)
    return dbm_entries
