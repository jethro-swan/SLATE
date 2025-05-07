#!/home/slate/SLATE/venv/bin/python3

import os
import sys
import argparse
#import re
#from app.core.slate_core import identify_entity, get_entity_type
from app.core.common import nshash
from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph
from app.core.slate_core import get_entity_type
from app.core.constants import DB_DIR
from app.core.constants import MAP_BKP_DIR, FPH_TO_HRNS_MAP, HRNS_C_FPH_MAP
from app.core.dbm_functions import dbm_store, dbm_fetch
from app.core.dbm_functions import dbm_delete, dbm_keys, dbm_list_entries
from app.core.display import Yn, yN

script_name = sys.argv[0].replace(".py", "").replace("./", "")
script_name = script_name.replace("/usr/local/bin/", "")

p = argparse.ArgumentParser(description = "Check FPH-HRNS mapping consistency")
p.add_argument(
    "-l", "--list-entries", dest = "list_entries", action = "store_true",
    help = "Show all FPH-HRNS pairs"
)
p.add_argument(
    "-r", "--repair", dest = "repair_entries", action = "store_true",
    help = "Repair entries from HRNS"
)
p.add_argument(
    "-c", "--confirm-repair", dest = "confirm_repair", action = "store_true",
    help = "Confirm suggested repair"
)
args = p.parse_args()

if args.repair_entries or args.confirm_repair:
    print("Repair function not yet implemented")





all_fph = dbm_keys(FPH_TO_HRNS_MAP)
for fph in all_fph:
    hrns = fph_to_hrns(fph)
    hrns_ = hrns
    etype, em = get_entity_type(fph)
    if hrns == "":
        hrns = "[substrate]"
        etype = "substrate" # for display purposes
    fph_, m = hrns_to_fph(hrns_)
    #fph_ = "05a9d7bd4b47de131abe87e45f3c3356"
    e = ""
    if fph_ != fph:
        e = "inconsistent"
    if args.list_entries or (fph_ != fph):
        print("{:<12} {} > {:<50} {:<20} {}".format(etype, fph, hrns, e, m))
    if args.repair_entries and (fph_ != fph):
        if (not args.confirm_repair) or yN("Repair mapping?"):
            dbm_delete(FPH_TO_HRNS_MAP, fph)
            dbm_delete(HRNS_C_FPH_MAP, hrns)
            fph, m = hrns_to_fph(hrns)
            if m:
                print(m)
            print(hrns + " re-mapped to " + fph)
            hrns_ = fph_to_hrns(fph)
            if hrns_ != hrns:
                print("Inconsistency found after re-mapping")
