#!/home/slate/SLATE/venv/bin/python3


import sqlite3

from app.core.slate_core import list_currency_accounts
from app.core.slate_core import get_account_currency
from app.core.slate_core import get_account_specific_properties
from app.core.slate_core import identify_entity
from app.core.slate_core import random_filename
from app.core.constants import GRAPHS


def list_currency_payments(currency_id):

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_id)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified currency:
        cursor.execute(
            """
            SELECT timestamp,
                   payment_id,
                   payer_fph,
                   payee_fph,
                   currency_fph,
                   amount,
                   payer_balance,
                   payee_balance,
                   annotation
            FROM payments
            WHERE currency_fph = ?
            """,
            (currency_fph,)
        )
        all_payments = cursor.fetchall()
        cursor.close()
    if all_payments is None:
        return []
