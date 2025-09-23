#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import pickle
import random

from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

from app.core.slate_core import new_namespace, new_currency, new_primid
from app.core.slate_core import split_hrns

from app.core.slate_core import new_pairing
from app.core.slate_core import retrieve_pmap
from app.core.slate_core import complete_parent_namespace
from app.core.payments import ah_payment

parent_fph, m = hrns_to_fph("cc")

primid_fph, m = hrns_to_fph("bb.cc")

robots_hrns_list = []
for i in range(10):
    robots_hrns_list.append("r" + str(i).zfill(2) + ".sand.box.cc")

for robot_hrns in robots_hrns_list:
    print(robot_hrns)

my_ahids_hrns_list = []
for name in ["ah1", "ah2", "ah3", "ah4"]:
    my_ahids_hrns_list.append(name + ".bb.cc")

currency_hrns_list = ["cc", "hrs.cc", "kwh.cc", "bb.cc"]

for n in range(100): # random payments to robot *ahid*s
    m = ah_payment(
            random.choice(my_ahids_hrns_list),
            random.choice(robots_hrns_list),
            random.choice(currency_hrns_list),
            random.randint(0, 100000),
            "test R" + str(n)
        )
#    if m:
#        print(m)
