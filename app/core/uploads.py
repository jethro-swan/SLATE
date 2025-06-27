import sqlite3
import os
import pickle
from pathlib import Path

from app.core.constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
from app.core.common import filename_timestamp as timestamp
from app.core.common import ledger_timestamp
from app.core.common import nshash

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps

from app.core.regexp_list import *

from app.core.unix_functions import fcopy

from app.core.slate_core import account_status
from app.core.slate_core import list_currencies_in_common_by_fph
from app.core.slate_core import list_currencies_in_common_by_hrns
from app.core.slate_core import identify_entity

from app.core.display import integer_to_money_format

from app import app

#==============================================================================
# Parse a CSV file containing instructions to create a set of *namespoaces*:
def csv_create_namespaces(csv_file):



    error_report = ""

    return error_report

#==============================================================================
# Parse a CSV file containing instructions to create a set of *login*:
def csv_create_identities(csv_file):



    error_report = ""

    return error_report

#==============================================================================
# Parse a CSV file containing instructions to create a set of *currencies*:
def csv_create_currencies(csv_file):



    error_report = ""

    return error_report

#==============================================================================
# Parse a CSV file containing instructions to create a set of *accounts*:
def csv_create_accounts(csv_file):



    error_report = ""

    return error_report

#==============================================================================
