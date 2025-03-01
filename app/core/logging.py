# Last modified: 2024-11-07 23.00 JW

import datetime
import os

from app.core.constants import SLATE_LOGS, LOG_DATETIME_FMT

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
                            "tests"
                           ]):
        return False
    timestamp = datetime.datetime.now().strftime(LOG_DATETIME_FMT)
    with open(SLATE_LOGS + category + ".log", "a") as log_file:
        log_file.write(timestamp + "\t" + summary + "\n")
        log_file.write(details + "\n")

#------------------------------------------------------------------------------
