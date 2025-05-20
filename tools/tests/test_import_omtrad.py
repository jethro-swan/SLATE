#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import pickle

from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

from app.core.slate_core import new_namespace, new_currency, new_primid
from app.core.slate_core import split_hrns

from app.core.omtrad import *



primid_fph, m = hrns_to_fph("bb.cc")

test_csv_import = True
if test_csv_import:

    fpath = "/home/slate/SLATE/csv_examples/import_datset_01.csv"

    report, errors = import_csv_dataset(fpath, primid_fph, SC=",")

    print()
    if report is None:
        print("Invalid report list")
    elif isinstance(report, list):
        for row in report:
            print(row)
    else:
        print("Invalid report list")
    print()
    if errors is None:
        print("Invalid errors list")
    elif isinstance(errors, list):
        for row in errors:
            print(row)
    else:
        print("Invalid errors list")
    print()


    pmap, m = retrieve_pmap(primid_fph)
    print(pmap)
