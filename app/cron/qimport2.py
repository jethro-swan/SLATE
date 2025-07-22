#!/home/slate/SLATE/venv/bin/python3
#
# This file is run as a cron task

import os, sys
from pathlib import Path

from app.core.slate_core import split_hrns
from app.core.slate_core import import_csv_dataset
from app.core.common import ledger_timestamp
from app.core.constants import IMPORT_QUEUE, IMPORTING, SLATE_TEMP

from app.core.common import unixtime_str

# If another import operation is in progress, exits.

if not os.path.exists(IMPORT_QUEUE):
    sys.exit()
if os.path.exists(IMPORTING):
    if not os.path.exists(IMPORT_QUEUE):
        os.unlink(IMPORTING)
        sys.exit()
    if os.path.getsize(IMPORT_QUEUE) == 0:
        os.unlink(IMPORTING)
        sys.exit()
# Otherwise, block any other import operation for the time being.
Path(IMPORTING).touch()

with open(IMPORT_QUEUE, "r") as iqf:
#    niq = iqf.readline() # read one line
    queued_imports = iqf.readlines() # read all lines

#if niq:
#    with open(IMPORT_QUEUE, "r+") as iqf:
#        iqf.seek(0) # return to the beginning
#        lines = iqf.readlines() # read all lines into a list
#        iqf.seek(0) # return to the beginning
#        iqf.truncate() # remove all lines
#        iqf.writelines(lines[1:]) # write all lines except first back from list

for niq in queued_imports:

    next_in_queue = niq.strip().split(":")
    primid_fph = next_in_queue[0]
    filename = next_in_queue[1]
    fpath = SLATE_TEMP + "/" + filename
    report, errors = import_csv_dataset(fpath, primid_fph)
    os.unlink(fpath)

    with open(SLATE_TEMP + "/" + "import_log", "a") as import_log:
        #log_line = ledger_timestamp() + ":" + primid_fph + "\n"
        import_log.write(ledger_timestamp() + ":" + primid_fph + "\n")
        for line in report:
            import_log.write(line + "\n")
        for line in errors:
            import_log.write(line + "\n")

os.unlink(IMPORTING)
