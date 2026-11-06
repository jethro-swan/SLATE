#!/home/slate/SLATE/venv/bin/python3

# NESTS/SLATE - a networked tool to support user-created and -stewarded
# currencies and measures (open money and open measure)
# Copyright (C) 2026. 2025, 2024, 2023, 2022 John Waters
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import sqlite3
import os
import math

from app.core.slate_core import retrieve_pairing_account_fph
from app.core.slate_core import identify_entity
from app.core.slate_core import list_currency_accounts
from app.core.slate_core import get_account_currency
from app.core.slate_core import random_filename
from app.core.slate_core import get_account_properties

from app.core.display import integer_to_money_format

from app.core.constants import GRAPHS
from app.core.constants import PAYMENTS_DB

from bokeh.models import ColumnDataSource
from bokeh.palettes import Bright6
from bokeh.plotting import figure, show
from bokeh.plotting import figure
from bokeh.io import export_png
from bokeh.io import export_svg

#==============================================================================
# A plot is created from the list of *accounts* (balance, volume) tuples
# assembled from ahid_fph and currency_fph provided. If plot_other_accounts is
# true, all other *accounts* in the same *currency* to be included as points in
# the same plot.

def create_balvol_plot(currency_id, ahid_id, plot_other_accounts = False):
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not (currency_fph and ("currency" in etypes)):
        return "", ""
    ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_id)
    if not (ahid_fph and ("ahid" in etypes)):
        return "", ""

    account_fph, primid_fph, \
    m = retrieve_pairing_account_fph(ahid_hrns, currency_fph)

    account_currency_fph, account_owner_fph, account_balance, account_volume, \
    account_active, account_type, account_category, account_units, \
    account_metrical_equivalence, account_dimensions, \
    m = get_account_properties(account_fph)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified currency:
        if plot_other_accounts:
            cursor.execute(
                "SELECT payer_fph, payee_fph, payer_balance, " \
                + "payer_volume, payee_balance, payee_volume " \
                + "FROM payments WHERE currency_fph = ?",
                (currency_fph,)
            )
        else:
            cursor.execute(
                "SELECT payer_fph, payee_fph, payer_balance, " \
                + "payer_volume, payee_balance, payee_volume " \
                + "FROM payments WHERE (payer_fph = ? OR payee_fph = ?) " \
                + "and (currency_fph = ?)",
                (ahid_fph, ahid_fph, currency_fph)
            )
        all_payments = cursor.fetchall()
        cursor.close()
    if all_payments is None:
        return "", ""

    other_plot_points = []
    own_plot_points = []
    for payment in all_payments:
        p = list(payment)
        payer_fph = p[0]
        payee_fph = p[1]
        payer_balance = integer_to_money_format(p[2])
        payer_volume = integer_to_money_format(p[3])
        payer_plot_point = (payer_balance, payer_volume)
        payee_balance = integer_to_money_format(p[4])
        payee_volume = integer_to_money_format(p[5])
        payee_plot_point = (payee_balance, payee_volume)
        if payer_fph == ahid_fph: # payment
            if not (payer_plot_point in own_plot_points):
                own_plot_points.append(payer_plot_point)
        elif payee_fph == ahid_fph: # receipt
            if not (payee_plot_point in own_plot_points):
                own_plot_points.append(payee_plot_point)
        else:
            if not ((payer_balance, payer_volume) in other_plot_points):
                other_plot_points.append((payer_balance, payer_volume))
            if not ((payee_balance, payee_volume) in other_plot_points):
                other_plot_points.append((payee_balance, payee_volume))

    margin = 2 # pixels -- offset
    X_width = 350 # pixels
    X0 = X_width // 2
    Y_height = X0 # pixels

    # TESTSTUFF
    sd_count = 0
    sd_sum = 0
    sd = 0

    bal_min = bal_max = 0
    pp2 = []
    for plot_point in own_plot_points:
        bal = int(100*float(plot_point[0]))
        vol = int(100*float(plot_point[1]))
        bal_min = min(bal_min, bal)
        bal_max = max(bal_max, bal)
        pp2.append((bal, vol))

        # TESTSTUFF
        sd_sum += bal*bal
        sd_count += 1

    # If we are plotting the (balance, volume) values of other *accounts*,
    # these must be accommodated in the autoscaling without polluting the
    # *account* in focus.
    if plot_other_accounts:
        pp2a = []
        for plot_point in other_plot_points:
            bal = int(100*float(plot_point[0]))
            vol = int(100*float(plot_point[1]))
            bal_min = min(bal_min, bal)
            bal_max = max(bal_max, bal)
            pp2a.append((bal, vol))

        # TESTSTUFF
        sd_sum += bal*bal
        sd_count += 1
        if sd:
            sd = math.sqrt(sd_sum/sd_count)

    bal_lim = max(abs(bal_min), abs(bal_max))
    if bal_lim == 0:
        return "", "" # unable to plot graph

    print("\nbal_min = " + str(bal_min))
    print("bal_max = " + str(bal_min))
    print("sd_count = " + str(sd_count))
    print("sd = " + str(sd))
    if sd:
        print("bal_lim/sd = " + str(bal_lim/sd))

    bal_scale = X0/bal_lim

    plot_filename = random_filename() + ".svg"
    graph_path = GRAPHS + ahid_fph + "/"
    if not os.path.exists(graph_path):
        os.mkdir(graph_path, 0o770)
    plot_path = graph_path + plot_filename
#    plot_path = GRAPHS + ahid_fph + "/" + plot_filename

    pp3 = [(0, 0)] # Start at the origin (0, 0)
    y = 0
    for p in pp2:
        x = round(p[0]*bal_scale)
        y = p[1]
        pp3.append((x, y))


    if plot_other_accounts:
        pp3a = [(0, 0)] # Start at the origin (0, 0)
        y = 0
        for p in pp2a:
            x = round(p[0]*bal_scale)
            y = p[1]
            pp3a.append((x, y))

    if plot_other_accounts:
        v_max = max(pp3[-1][1], pp3a[-1][1])
    else:
        v_max = pp3[-1][1] # the y value of the last element in the list
    v_scale = Y_height/v_max
    with open(plot_path, "w") as pf:
        pf.write(
            '<?xml version="1.0" standalone="no"?> ' \
            + '<svg xmlns="http://www.w3.org/2000/svg" version="1.1" ' \
            + 'width="' + str(margin + X_width + margin) + '" ' \
            + 'height="' + str(margin + Y_height) + '"> ' \
            + '<style>' \
            + '  text {' \
            + '   font-family: Verdana,Helvetica,sans-serif;' \
            + '   font-weight: normal;' \
            + '   font-size:0.8em;' \
            + '  } ' \
            + '</style> ' \
            + '<line x1="' + str(margin + X0) + '" ' \
            + 'y1="' + str(margin) + '" ' \
            + 'x2="' + str(margin + X0) + '" ' \
            + 'y2="' + str(margin + Y_height) + '" ' \
            + 'style="stroke:black;stroke-width:1" /> ' \
            + '<text x="' + str(margin + X0 + 10) + '" ' \
            + 'y="' + str(margin + 10) + '" ' \
            + '>volume</text> '
            + '<line x1="' + str(margin) + '" ' \
            + 'y1="' + str(margin + Y_height) + '" ' \
            + 'x2="' + str(margin + X_width) + '" ' \
            + 'y2="' + str(margin + Y_height) + '" ' \
            + 'style="stroke:black;stroke-width:1" /> ' \
            + '<text x="' + str(margin + 2*X0 - 50) + '" ' \
            + 'y="' + str(margin + Y_height - 8) + '" ' \
            + '>balance</text>'
        )
        p_from = pp3.pop()
        while len(pp3) > 0:
            p_to = pp3.pop()
            x_from = str(margin + p_from[0] + X0)
            y_from = str(margin + Y_height - round(p_from[1]*v_scale))
            x_to = str(margin + p_to[0] + X0)
            y_to = str(margin + Y_height - round(p_to[1]*v_scale))
            pf.write(
                '<circle cx="' + x_from + '" cy="' + y_from + '" r="3" /> ' \
                + '<circle cx="' + x_to + '" cy="' + y_to + '" r="3" /> ' \
                + '<line x1="' + x_from + '" y1="' + y_from + '" ' \
                + 'x2="' + x_to + '" y2="' + y_to + '" ' \
                + 'style="stroke:black;stroke-width:1" />'
            )
            p_from = p_to
        #
        if plot_other_accounts:
            p = pp3a.pop()
            while len(pp3a) > 0:
                p = pp3a.pop()
                x = str(margin + p[0] + X0)
                y = str(margin + Y_height - round(p[1]*v_scale))
                pf.write(
                    '<circle cx="' + x + '" cy="' + y + '" ' \
                    + 'r="2.5" fill="grey" />'
                )

        pf.write('</svg>')

    return plot_filename, graph_path

#==============================================================================

def currency_balance_graphs(currency_id):
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not ("currency" in etypes):
        return ""

    account_fph_list = list_currency_accounts(currency_fph)

    balances = []
    volumes = []
    a = []
    x_ = 1 # x axis: count of *accounts*
    b_max = b_min = 0
    v_max = v_min = 0
    for account_fph in account_fph_list:
        currency_fph, owner_fph, balance, volume, active, \
        account_type, account_category, account_units, \
        account_metrical_equivalence, account_dimensions, \
        m = get_account_properties(account_fph)
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

#    b_imgpath = GRAPHS + random_filename() + ".png"
#    v_imgpath = GRAPHS + random_filename() + ".png"
    b_imgpath = GRAPHS + random_filename() + ".svg"
    v_imgpath = GRAPHS + random_filename() + ".svg"

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

#    export_png(b, filename = b_imgpath)
#    export_png(v, filename = v_imgpath)
    export_svg(b, filename = b_imgpath)
    export_svg(v, filename = v_imgpath)

    return b_imgpath, v_imgpath
