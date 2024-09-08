import dbm
from base64 import b64encode

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
        for k in db.keys():
            key = k.decode("utf-8")
            value = db[k].decode("utf-8")
            print(key + " \t" + value)
