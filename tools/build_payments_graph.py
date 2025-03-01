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
    "#000000", "#ff0000", "#ff7f00", "#ffff00", "#00ff00",
    "#0000ff", "#4b0082", "#8f00ff"

]


input_filename = "payments_made"

with open("temp/" + input_filename, "r") as f:
    payments_list = f.readlines()

for payment_row in payments_list:
    p = payment_row.strip().split(":")
    payer_account_fph = p[0]
    payer_identity_fph = p[1]
    payee_identity_fph = p[2]
    payee_account_fph = p[3]
    currency_fph = p[4]
    amount = p[5]
    print(
        "Payment from account " + fph_to_hrns(payer_account_fph) \
        + " to account " + fph_to_hrns(payer_identity_fph) \
        + " (from identity " + fph_to_hrns(payee_account_fph) \
        + " to identity " + fph_to_hrns(payee_identity_fph) + ")" \
        + " of " + amount + " in currency " + fph_to_hrns(currency_fph)
    )


#-------------------------------------------------------------------------------
# The data directory tree is created if it does not exist already:
if not os.path.exists(data_dir):
    os.mkdir(data_dir)
if not os.path.exists(data_dir + "/gv"):
    os.mkdir(data_dir + "/gv")
if not os.path.exists(data_dir + "/output"):
    os.mkdir(data_dir + "/output")






# os.system("dot -Tpng " + gvfile2 + " -o " + gpath)
