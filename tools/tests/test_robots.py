#!/home/slate/SLATE/venv/bin/python3

from app.core.robots import get_next_robot_receipt
from app.core.robots import send_next_robot_response
from app.core.robots import robots_respond

from app.core.flags import set_flag, unset_flag

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns


set_flag("run_robots")
#robots_loop()
#payee_robot_fph, payer_ahid_fph, \
#currency_fph = get_next_robot_receipt()

#still_in_queue = send_next_robot_response()
#print("still_in_queue = " + str(still_in_queue))

robots_respond()

#if payer_ahid_fph:
#    print(
#        "robot " + fph_to_hrns(payee_robot_fph) + " was sent a payment of " \
#        + fph_to_hrns(currency_fph) + " by " + fph_to_hrns(payer_ahid_fph)
#    )
