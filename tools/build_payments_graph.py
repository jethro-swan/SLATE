#!/home/john/NESTS/SLATE/venv/bin/python3
# -*- coding: utf-8 -*-
#
#  islands.py
#
#  Copyright 2023 John Waters <john.waters@lrc.org.uk>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.


#===============================================================================
# This is a ridiculously simple script to generate payments between two
# randomly-selected agents. The payments may be either fixed at 1 (the default)
# or randomly-generated within a defined range.
#
# All agents have access to a default money ("legal tender" - LT) usable between
# any of them. This is what they have to use unless they share access to an
# island money.
#
# In this simulation, there may be up to 10,000 agents (100 by default, numbered
# 0 to 99) and up to 9 "island" monies (1, 4 or 9, excluding the LT "island 0").
#
# For the sake of simplicity, the monies (including LT) are identified by the
# 10s digit (0 being LT). However, the method of distinction is arbitrary and
# other options may be added in due course.

import datetime, time
import os
import shutil
import random
import argparse
#import numpy as np
#import matplotlib.pyplot as plt
#from matplotlib.figure import Figure
#from matplotlib.ticker import MaxNLocator

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.common import filename_timestamp as timestamp
from app.core.slate_core import account_status
from app.core.payments import payment
from app.core.common import filename_timestamp
from app.core.display import integer_to_money_s_format



data_dir = "temp"

colours = [
    "#ff0000",  # red
    "#ff8000",  # orange
    "#4c9900",  # green
    "#006666",  # tealish
    "#0066cc",  # blue
    "#330066",  # indigoish
    "#4c0099",  # violet
    "#994c00",  # yellowish ochre
    "#ffff00",  # yellow
    "#9999ff"   # lilacish
]

colour_index = 0
colour_map = {}
with open("temp/currencies_created", "r") as f:
    currencies_list = f.readlines()
    for currency_fph in currencies_list:
        colour_map[currency_fph.strip()] = colours[colour_index]
        colour_index += 1

#-------------------------------------------------------------------------------
# The data directory tree is created if it does not exist already:
if not os.path.exists(data_dir):
    os.mkdir(data_dir)
if not os.path.exists(data_dir + "/gv"):
    os.mkdir(data_dir + "/gv")
if not os.path.exists(data_dir + "/output"):
    os.mkdir(data_dir + "/output")
gvdir = data_dir + "/gv/"
gvfile = gvdir + "pgraph.dot"
gpng = gvdir + "pgraph" + filename_timestamp() + ".png"
gsvg = gvdir + "pgraph" + filename_timestamp() + ".svg"

input_filename = "payments_made"

with open("temp/" + input_filename, "r") as f:
    payments_list = f.readlines()


# The GraphViz DOT file is opened:
gvf = open(gvfile, "w")
gvf.write(
        "digraph payments {\n" \
        + "\trankdir=LR\n" \
        + "\tnode [shape=circle]\n" \
        + "\tfontsize=\"30\"\n"
    )
# Added to remove need to show HRNS in node labels:
node_label = {}
node_number = 0

for payment_row in payments_list:
    p = payment_row.strip().split(":")
    payer_account_fph = p[0]
    payer_account_hrns = fph_to_hrns(payer_account_fph)
    payer_identity_fph = p[1]
    payer_identity_hrns = fph_to_hrns(payer_identity_fph)
    payee_account_fph = p[2]
    payee_account_hrns = fph_to_hrns(payee_account_fph)
    payee_identity_fph = p[3]
    payee_identity_hrns = fph_to_hrns(payee_identity_fph)
    currency_fph = p[4]
    currency_hrns = fph_to_hrns(currency_fph)
    amount = p[5]
    edge_colour = colour_map[currency_fph]

    if not (payer_identity_fph in node_label.keys()):
        node_label[payer_identity_fph] = str(node_number).zfill(3)
        node_number += 1
    if not (payee_identity_fph in node_label.keys()):
        node_label[payee_identity_fph] = str(node_number).zfill(3)
        node_number += 1
#    print(node_label)
#    gvf.write(
#        "\t"
#        + "\"" + payer_identity_hrns + "\" -> \"" + payee_identity_hrns \
#        + "\" [color=\"" + edge_colour + "\"" \
#        + " penwidth=\"2.0\" fontname=\"Verdana\"]\n"
#    )
    gvf.write(
        "\t\"" \
        + node_label[payer_identity_fph] \
        + "\" -> \"" \
        + node_label[payee_identity_fph] \
        + "\" [color=\"" + edge_colour + "\"" \
        + " penwidth=\"2.0\" fontname=\"Verdana\"]\n"
    )
gvf.write("}\n")
gvf.close()


os.system("dot -Tpng " + gvfile + " -o " + gpng)
#os.system("dot -Tsvg " + gvfile + " -o " + gsvg)
