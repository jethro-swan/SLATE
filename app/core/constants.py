# Last modified: 2025-08-29 17.55 JW

import xxhash
#from .common import nshash
def nshash(name): # Defined again here to avoid circular import from common.py
    return xxhash.xxh3_128_hexdigest(name.strip())

SLATE_DATA_ROOT     = "/var/slate/active/data/"
SLATE_DATA          = "/var/slate/active"
SLATE_TEMP          = "/var/slate/active/temp"
IMPORT_QUEUE        = "/var/slate/active/temp/import_queue"
IMPORTING           = "/var/slate/active/temp/importing"
GRAPHS              = "/home/slate/SLATE/app/static/graphs/"


SLATE_MAPS          = SLATE_DATA + "/maps/"      #
QR_CODES            = "/home/slate/SLATE/app/static/qr/" # QR codes generated
                                                # (both cleared out regularly)
# logging files
SLATE_LOGS          = SLATE_DATA + "/logs/"
DEBUG_LOG           = SLATE_LOGS + "debug.log"
ERROR_LOG           = SLATE_LOGS + "error.log"
AUTH_LOG            = SLATE_LOGS + "auth.log"
ACTIVITY_LOG        = SLATE_LOGS + "activity.log"
SLATE_LOGS_BKP_DIR  = SLATE_LOGS + "backups/"

# Formatting:
NS_SEPARATOR        = "."
NSS                 = "."
TIMESTAMP_FMT       = "%Y-%m-%d %H:%M (%A)"
FNAME_DATETIME_FMT  = "%Y-%m-%d_%H%M%S%f"
LOG_DATETIME_FMT    = "%Y-%m-%d %H:%M:%S:%f"
LEDGER_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"

# Database directory (SQLite and DBM):
DB_DIR              = "/var/slate/active/db/"
DB_BKP_DIR          = "/var/slate/active/db/backups/"

# SQLite database files:
HUBS_DB             = "/var/slate/active/db/hubs.db"
ENTITIES_DB         = "/var/slate/active/db/entities.db"
PAYMENTS_DB         = "/var/slate/active/db/payments.db"
SLATE_SESSION_DB    = "/var/slate/active/db/slate_session.db"
MESSAGES_DB         = "/var/slate/active/db/messages.db"
HUBS_DB             = "/var/slate/active/db/hubs.db"

# DBM maps:
MAP_BKP_DIR         = "/var/slate/active/maps/backups/"
FPH_TO_HRNS_MAP     = "/var/slate/active/maps/FPH_to_HRNS_map.dbm"
HRNS_C_FPH_MAP      = "/var/slate/active/maps/FPH_to_HRNS_collision_map.dbm"
CONFIG_MAP          = "/var/slate/active/maps/config_map.dbm"

SUBSTRATE_FPH       = nshash("")

# Temporary kludge:
VERSION             = "/home/slate/SLATE/version"
CONFIG              = "/home/slate/SLATE/hub_config"
