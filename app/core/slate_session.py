import os
import sqlite3
import pickle

from .constants import ENTITIES_DB, SLATE_SESSION_DB, DB_BKP_DIR

from .common import filename_timestamp as timestamp
from .common import nshash

from .unix_functions import fcopy

from flask import session

#==============================================================================
## Create the SQLite slate_session database:
##
## This is used to hold session data too large for Flask's session cookies to
## accommodate (i.e. not transferable via the  session[ ] dictionary).
##
## User-specific session data are
## - created upon logging in
## - deleted upon logging out
## - preserved between stopping and restarting the application
## Therefore users will not be logged out simply because the application has
## been stopped and restarted to apply changes to the code (although they will
## experience a brief delay in response while the application restarts).
##
## (It may be helpful to broadcast an explanatory message to all users
## currently logged in, however).
##
## Saving the  currencies_list[ ]  list here removes the need to regenerate it
## unless a new **currency** has been added during the session.
##
## Saving the  payment_options  dictionary here removes the need to regenerate
## it unless a new **currency**, **account** or *8alias** has been added during
## the session.

def create_slate_session_db():
    if os.path.exists(SLATE_SESSION_DB):
        # If the database exists already, it is deleted after a time-stamped
        # copy has been saved.
        fcopy(
            SLATE_SESSION_DB, DB_BKP_DIR + '/slate_session_' \
            + timestamp() + '.db'
        )
        os.remove(SLATE_SESSION_DB)

    with sqlite3.connect(SLATE_SESSION_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
    	    CREATE TABLE IF NOT EXISTS slate_session (
                session_id TEXT PRIMARY KEY,
                currencies_available BLOB,
                payment_options BLOB,
                payer_accounts_available BLOB,
                payee_accounts_available BLOB
            );
            """
        )
        conn.commit()
        cursor.close()
    return


#==============================================================================
#
def session_save_currencies_available(currencies_available, payment_options):
    #session_id = session["_id"] # from session dictionary
    with sqlite3.connect(SLATE_SESSION_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM slate_session WHERE session_id = ?",
            (session["_id"],) # from session dictionary
        )
        cursor.execute(
            """
            INSERT INTO slate_session (
                session_id,
                currencies_available,
                payment_options
            )
            VALUES (?, ?, ?)
            """,
            (
                session["_id"], # from session dictionary
                pickle.dumps(currencies_available),
                pickle.dumps(payment_options)
            )
        )
        conn.commit()
        cursor.close()
    return

#------------------------------------------------------------------------------
#
def session_retrieve_currencies_available():
    with sqlite3.connect(SLATE_SESSION_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT currencies_available, payment_options
            FROM slate_session
            WHERE session_id = ?
            """,
            (session["_id"],) # from session dictionary
        )
        result = cursor.fetchone()
        cursor.close()
    if result is None:
        return [], [], "Currency options unavailable"
    m = ""
    if result[0] is None:
        currencies_available = []
        m = "No currencies available"
    else:
        currencies_available = pickle.loads(result[0])
    if result[1] is None:
        payment_options = []
        m = "No payment options available"
    else:
        payment_options = pickle.loads(result[1])
    return currencies_available, payment_options, m

#==============================================================================
#
def session_save_payment_options(payer_account_options, payee_account_options):
    with sqlite3.connect(SLATE_SESSION_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT session_id FROM slate_session")
        result = cursor.fetchone()
        if result is not None:
            cursor.close()
            return
        session_id = session["_id"] # from session dictionary
        cursor.execute(
            """
            INSERT INTO slate_session (
                session_id,
                payer_accounts_available,
                payee_accounts_available
            )
            VALUES (?, ?, ?)
            """,
            (
                session["_id"], # from session dictionary
                pickle.dumps(payer_account_options),
                pickle.dumps(payee_account_options)
            )
        )
        conn.commit()
        cursor.close()
    return

#==============================================================================
#
def session_retrieve_payment_options():
    with sqlite3.connect(SLATE_SESSION_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT payer_accounts_available, payee_accounts_available
            FROM slate_session
            WHERE session_id = ?
            """,
            (session["_id"],) # from session dictionary
        )
        result = cursor.fetchone()
#        cursor.execute(
#            "DELETE FROM slate_session WHERE session_id = ?",
#            (session["_id"],) # from session dictionary
#        )
        cursor.close()
        if result is None:
            #return {}, {}, "Payment options unavailable"
            return [], [], "Payment options unavailable"
        if result[0] is None:
            payer_account_options = []
        else:
            payer_account_options = pickle.loads(result[0])
        if result[1] is None:
            payee_account_options = []
        else:
            payee_account_options = pickle.loads(result[1])
    return payer_account_options, payee_account_options, ""

#------------------------------------------------------------------------------

#def session_retrieve_payee_accounts_available():
#    with sqlite3.connect(SLATE_SESSION_DB) as conn:
#        cursor = conn.cursor()
#        cursor.execute(
#            """
#            SELECT payee_accounts_available
#            FROM slate_session
#            WHERE session_id = ?
#            """,
#            (session["_id"],) # from session dictionary
#        )
#        result = cursor.fetchone()
#        cursor.execute(
#            "DELETE FROM slate_session WHERE session_id = ?",
#            (session["_id"],)
#        )
#        cursor.close()
#        if result is None:
#            return [], {}, "No payee accounts available"
#        payee_accounts_available = pickle.loads(result[0])
#    return payee_accounts_available, ""


#==============================================================================
#
def remove_slate_session_data():
    with sqlite3.connect(SLATE_SESSION_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM slate_session WHERE session_id = ?",
            (session["_id"],) # from session dictionary
        )
    return

#==============================================================================
