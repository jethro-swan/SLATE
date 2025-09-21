#!/home/slate/SLATE/venv/bin/python3

from app.core.constants import ROBOTS_LIST



from app.core.robots import create_robots_db
from app.core.robots import create_robots
#from app.core.robots import robots_loop
from app.core.robots import get_next_robot_receipt
from app.core.robots import send_next_robot_response

from app.core.flags import set_flag, unset_flag

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns

#create_robots_db()

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


set_flag("run_robots")
#robots_loop()
#payee_robot_fph, payer_ahid_fph, \
#currency_fph = get_next_robot_receipt()

send_next_robot_response()

#if payer_ahid_fph:
#    print(
#        "robot " + fph_to_hrns(payee_robot_fph) + " was sent a payment of " \
#        + fph_to_hrns(currency_fph) + " by " + fph_to_hrns(payer_ahid_fph)
#    )
