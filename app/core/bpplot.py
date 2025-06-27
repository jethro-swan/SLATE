#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import list_currency_accounts
from app.core.slate_core import get_account_currency
from app.core.slate_core import get_account_specific_properties
from app.core.slate_core import identify_entity
from app.core.slate_core import random_filename

from app.core.constants import GRAPHS, PAYMENTS_DB

from bokeh.models import ColumnDataSource
from bokeh.palettes import Bright6
from bokeh.plotting import figure, show
from bokeh.plotting import figure
from bokeh.io import export_svg

import sqlite3

def account_balance_oscillation(ahid_hrns, currency_hrns):

    ahid_fph, ahid_hrns, etype, m = identify_entity(ahid_hrns)
    if etype != "ahid":
        return "", ""

    currency_fph, currency_hrns, etype, m = identify_entity(currency_hrns)
    if etype != "currency":
        return "", ""

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified currency:
        cursor.execute(
            """
            SELECT payer_fph, payee_fph, amount
            FROM payments
            WHERE currency_fph = ? AND (payer_fph = ? OR payee_fph = ?)
            """,
            (currency_fph, ahid_fph, ahid_fph)
        )
        all_payments = cursor.fetchall()
        cursor.close()

    if all_payments is None:
        return [], ""

#    print(all_payments)

    X = []  # list of x co-ordinatate
    Y = []  # list of corresponding y co-ordinatate
            #   -B < x < B, B is abs(b_max)
            #   0 < y < N, N is number of trasactions
    ab_min = ab_max = ab = 0.0
    n = 0
    for row in all_payments:
        amount = row[2]
        if row[0] == ahid_fph: # this *account* is the payer
            ab -= amount
            ab_min = min(ab_min, ab)
        else: # this *account* is the payee
            ab += amount
            ab_max = max(ab_max, ab)
        X.append(ab)
        Y.append(n)
        n += 1
    B = max(ab_max, -ab_min)
    X_min = -B
    X_max = B
    for i in range(len(X)):
        print("(" + str(X[i]) + "," + str(Y[i]) + ")")

    print(str(X_min) + ", " + str(X_max))
    print(str(n))

    return "", ""


    b_imgpath = GRAPHS + random_filename() + ".svg"
    v_imgpath = GRAPHS + random_filename() + ".svg"

    b = figure(
            x_range = (X_min, X_max),
            width = 600,
            height = 600,
            toolbar_location = None,
            tools = ""
        )

    b.xaxis.visible = False
    b.yaxis.visible = False

    b.vbar(
        x = (X_min, X_max),
        top = X,
        line_color = "#ffffff",
        width = 0.9
    )

    b.x_range.range_padding = 0.0

    v = figure(
            x_range = a,
            width = 600,
            height = 600,
            toolbar_location = None,
            tools = ""
        )

    v.xaxis.visible = False
    v.yaxis.visible = False
    v.vbar(x = a, top = volumes, line_color = "#ffffff", width = 0.9)
    v.x_range.range_padding = 0.0

    export_svg(b, filename = b_imgpath)
    export_svg(v, filename = v_imgpath)

    return b_imgpath, v_imgpath
