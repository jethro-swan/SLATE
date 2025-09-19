#!/home/slate/SLATE/venv/bin/python3

from app.core.constants import ROBOTS_LIST

from app.core.robots import create_robots_db
from app.core.robots import create_robots


#create_robots_db()

n_robots = 100
robot_parent = "box.cc"

if create_robots(number_of_robots=80, robot_parent="sand.box.cc"):

    #print("Creating " + str(n_robots) + " in namespace " + robot_parent)

    with open(ROBOTS_LIST, "r") as rl:
        robots_list = rl.readlines()

    for robot_hrns in robots_list:
        print(robot_hrns.strip())

else:
    print("No robots created")
