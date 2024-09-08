# Last modified: 2023-07-12 18.50 JW

import datetime
import os

#from core.constants import *

#------------------------------------------------------------------------------
# Log an event:
#
def log_event(category, summary, details):
    if category not in set(["access",
                            "activity",
                            "auth",
                            "debug",
                            "entity_history",
                            "error",
                            "tests"]):
        return False
    timestamp = datetime.datetime.now().strftime(LOG_DATETIME_FMT)
    with open(NESTS_LOGS + "/" + category + ".log", "a") as log_file:
        log_file.write(timestamp + "\t" + summary + "\n")
        log_file.write(details + "\n")

#------------------------------------------------------------------------------
