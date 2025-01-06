import sqlite3
import os
import pickle
from pathlib import Path

from .constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, DB_BKP_DIR
from .common import filename_timestamp as timestamp
from .common import ledger_timestamp
from .common import nshash

from .fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps

from .regexp_list import *

from .unix_functions import fcopy

from .slate_core import account_status
from .slate_core import list_currencies_in_common_by_fph
from .slate_core import list_currencies_in_common_by_hrns
from .slate_core import identify_entity

from .display import integer_to_money_format

from app import app


@app.route("/import/create/namespaces", methods = ["GET", "POST"])
@login_required
def import_create_namespaces():

    # Display link to file upload dialogue

    # Upload CSV file containing instructions to create a set of *namespaces*
    # from the following fields:
    # - name
    # - parent *namespace*
    # - initial steward (an existing *identity*)
    # - default *currency* for new registrations in this *namespace*

    # Parse the CSV file to create the *namespaces*

    return

#
@app.route("/import/create/identities", methods = ["GET", "POST"])
@login_required
def import_create_identities():

    # Display link to file upload dialogue

    # Upload CSV file containing instructions to create a set of *login
    # identities* from the following fields:
    # - name
    # - parent *namespace*
    # - *currency* for the initial *account*
    # - password (optional)  [auto-generated if none provided]
    # - PIN (optional)  [auto-generated if none provided]
    # - email address (required for access recovery purposes)

    # Parse the CSV file to create the *login identtiies*

    # Make a summary of the *login identities* created available (CSV) for
    # immediate download (required because some password and PIN may have been
    # auto-generated).

    return

#
@app.route("/import/create/currencies", methods = ["GET", "POST"])
@login_required
def import_create_currencies():

    # Display link to file upload dialogue

    # Upload CSV file containing instructions to create a set of *currencies*
    # from the following fields:
    # - name
    # - parent *namespace*
    # - initial steward (an existing *identity*)
    # - default name for new *accounts* created in this *currency*
    # - a display prefix (optional)
    # - a display suffix (optional)

    # Parse the CSV file to create the *currencies*

    return

#
@app.route("/import/create/accounts", methods = ["GET", "POST"])
@login_required
def import_create_accounts():

    # Display link to file upload dialogue

    # Upload CSV file containing instructions to create a set of *accounts*.
    # Each *account* pairs an *identity* with a *currency*, so the following
    # fields are needed:
    # - name
    # - parent *namespace*
    # - *currency*
    # - *identity* (of the *accounts*'s owner)

    # Parse the CSV file to create the *accounts*

    return

#
@app.route("/import/create/payments", methods = ["GET", "POST"])
@login_required
def import_create_payments():

    # Display link to file upload dialogue

    # Upload CSV file containing instructions to create a set of *payments*.
    #
    # Both payer and payee *accounts* can be identified either by *account*
    # identifier or by *identity*+*currency*, so the following fields are
    # needed:
    # - *currency* (only if neither payer *account* nor payee *account* given)
    # - payer *account* (only if *currency* and payer *identity* not specified)
    # - payer *identity* (only if payer *account* not specified)
    # - payee *account* (only if *currency* and payee *identity* not specified)
    # - payee *identity* (only if payee *account* not specified)
    #
    # The payments may be specified by different combinations of fields,
    # following precedence rules and checked for consistency.

    # Parse the CSV file to create the set of *payments*

    return
