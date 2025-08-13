import sqlite3
import os



#------------------------------------------------------------------------------
# In NESTS the FPH has so far been formed as the hash of the FIP, but making it
# the hash of the HRNS instead will simplify compatibility between SLATE and
# NESTS and speed up the HRNS to FPH mapping without having any signifcant
# impact on the FPH to HRNS and FPH to FIP mappings.

#==============================================================================
def create_hubs_db():

    # This database is kept separate from the others because it needs to be
    # kept consistent with copies held across other hubs (according to rules
    # not yet defined):

    if os.path.exists(HUBS_DB):
        # If the database exists already, it is deleted after a time-stamped
        # copy has been saved.
        fcopy(HUBS_DB, DB_BKP_DIR + '/entities_' + timestamp() + '.db')
        os.remove(HUBS_DB)
    #
    with sqlite3.connect(HUBS_DB) as conn:
        cursor = conn.cursor()
        # The initial values for the following details are read from a
        # configuration file at the time of installation.
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS hub (" \
            + "hub_id INTEGER PRIMARY KEY AUTOINCREMENT, " \
            + "subdomain TEXT DEFAULT '', " \
            + "must_be_archived INTEGER NOT NULL DEFAULT 1, " \
            + "administrators_fph_list BLOB, " \
            + "single_hub INTEGER NOT NULL DEFAULT 1, " \
            + "hub_members BLOB, " \
            + "synchronized_hubs BLOB, " \
            + "nests_extensions_enabled INTEGER NOT NULL DEFAULT 0, " \
            + "location_details BLOB, " \
            + "contact_details BLOB" \
            + ");"
        )

#==============================================================================
# Get hub mode:
#
# The operational mode is stored in an environment variable. Its value
# determines some aspects of the hub behaviour.

def get_hub_mode():
    hub_mode = os.environ.get("HUB_MODE")
    if hub_mode is None:
        return "omtrad"
    elif hub_mode in [
                        "slate_normal",
                        "slate_simple",
                        "slate_minimal",
                        "omtrad",
                        "nests"
                     ]:
        #print(hub_mode)
        return hub_mode
    else:
        return "omtrad"

# Get version number:
def get_version():
    with open(VERSION, "r") as v_file:
        version = v_file.read()
    return version


#==============================================================================
# Return site configuration item by key string:

def get_config():
    with open(CONFIG, "r") as cfg:
        c = cfg.readlines()
    config = {}
    for row in c:
        r = row.split()
        config[r[0]] = r[1]
    return config

#==============================================================================
