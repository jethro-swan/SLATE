#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import pickle

from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

from app.core.slate_core import new_namespace, new_currency, new_primid
from app.core.slate_core import split_hrns

from app.core.omtrad import *




if is_ancestor("mon.uk.cc", "uk.cc"):
    print("yes")
else:
    print("no")

if is_ancestor("chep.mon.uk.cc", "mon.uk.cc"):
    print("yes")
else:
    print("no")

if is_ancestor("bris.uk", "uk.cc"):
    print("yes")
else:
    print("no")
