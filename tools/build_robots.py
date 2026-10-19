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

from app.core.constants import ROBOTS_LIST

from app.core.robots import create_robots_db
from app.core.robots import create_robots

n_robots = 100
robot_parent = "box.cc"

we_need_robots = False

if we_need_robots:
    if create_robots(number_of_robots=80, robot_parent="sand.box.cc"):
        #print("Creating " + str(n_robots) + " in namespace " + robot_parent)
        with open(ROBOTS_LIST, "r") as rl:
            robots_list = rl.readlines()
        for robot_hrns in robots_list:
            print(robot_hrns.strip())
    else:
        print("No robots created")
else:
    print("No robots created")
