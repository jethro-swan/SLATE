#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import list_currency_accounts
from app.core.slate_core import get_account_currency
from app.core.slate_core import get_account_specific_properties
from app.core.slate_core import identify_entity
from app.core.slate_core import random_filename

from app.core.constants import GRAPHS

from bokeh.models import ColumnDataSource
from bokeh.palettes import Bright6
from bokeh.plotting import figure, show
from bokeh.plotting import figure
from bokeh.io import export_png


def currency_balance_graphs(currency_id):
    currency_fph, currency_hrns, etype, m = identify_entity(currency_id)
    if etype != "currency":
        return "", ""

    account_fph_list = list_currency_accounts(currency_fph)

    balances = []
    volumes = []
    a = []
    x_ = 1 # x axis: count of *accounts*
    b_max = b_min = 0
    v_max = v_min = 0
    for account_fph in account_fph_list:
        currency_fph, owner_fph, ahid_fph, balance, volume, \
        m = get_account_specific_properties(account_fph)
        balances.append(balance)
        volumes.append(volume)
        b_min = min(balance, b_min)
        b_max = max(balance, b_max)
        v_min = min(volume, v_min)
        v_max = max(volume, v_max)
        a.append(str(x_))
        x_ += 1
    b_min = b_max = max(b_min, b_max) # make symmetrical about x axis
    balances.sort()
    volumes.sort()

    b_imgpath = GRAPHS + random_filename() + ".png"
    v_imgpath = GRAPHS + random_filename() + ".png"

    b = figure(
            x_range = a,
            width = 600,
            height = 600,
            toolbar_location = None,
            tools = ""
        )

    b.xaxis.visible = False
    b.yaxis.visible = False

    b.vbar(
        x = a,
        top = balances,
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

    export_png(b, filename = b_imgpath)
    export_png(v, filename = v_imgpath)

    return b_imgpath, v_imgpath
