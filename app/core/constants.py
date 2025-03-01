# Last modified: 2024-10-13 17.20 JW

import xxhash
#from .common import nshash
def nshash(name): # Defined again here to avoid circular import from common.py
    return xxhash.xxh3_128_hexdigest(name.strip())

SLATE_DATA_ROOT     = "/var/slate/active/data/"
SLATE_DATA          = "/var/slate/active"
#SLATE_EXPORT        = "/srv/slate/export/"
#SLATE_IMPORT        = "/srv/slate/import/"
#SLATE_QR_CODES      = "/srv/slate/export/qr_codes/"

#SLATE_FLAGS         = SLATE_DATA + "flags/"     # The trailing / is important
#SLATE_TREES         = SLATE_DATA + "roots/"     # in this group.
#SLATE_FIXED         = SLATE_DATA + "fixed/"     #
SLATE_MAPS          = SLATE_DATA + "/maps/"      #
#SLATE_EXPORT        = SLATE_DATA + "export/"    # CSV exports
SLATE_WWW_OUT       = SLATE_DATA + "/www/"       # CSV exports
#SLATE_QR_CODES      = SLATE_DATA + "qr_codes/"  # QR codes generated
                                                # (both cleared out regularly)
# fixed values (symlinked files)
#ENABLED             = SLATE_FIXED + "enabled"   # f: = True
#DISABLED            = SLATE_FIXED + "disabled"  # f: = False

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
#LEDGER_DATETIME_FMT = "%Y-%m-%d %H:%M:%S:%f"
LEDGER_DATETIME_FMT = "%Y-%m-%d %H:%M:%S"

# Database directory (SQLite and DBM):
DB_DIR              = "/var/slate/active/db/"
DB_BKP_DIR          = "/var/slate/active/db/backups/"

# SQLite database files:
HUBS_DB             = "/var/slate/active/db/hubs.db"
ENTITIES_DB         = "/var/slate/active/db/entities.db"
#MAP_DB              = "/var/slate/db/map.db"
PAYMENTS_DB         = "/var/slate/active/db/payments.db"
SLATE_SESSION_DB    = "/var/slate/active/db/slate_session.db"
MESSAGES_DB         = "/var/slate/active/db/messages.db"
HUBS_DB             = "/var/slate/active/db/hubs.db"

# DBM maps:
MAP_BKP_DIR         = "/var/slate/active/maps/backups/"
FPH_TO_HRNS_MAP     = "/var/slate/active/maps/FPH_to_HRNS_map.dbm"
HRNS_C_FPH_MAP      = "/var/slate/active/maps/FPH_to_HRNS_collision_map.dbm"
#FPH_TO_HRNS_MAP     = "/var/slate/db/FPH_to_HRNS_map.dbm"
#HRNS_C_FPH_MAP      = "/var/slate/db/FPH_to_HRNS_collision_map.dbm"

SUBSTRATE_FPH       = nshash("")
