import sqlite3
import random
import os
import time
import threading
import multiprocessing
#import names

from app.core.constants import ROBOTS_DB
from app.core.constants import ROBOTS_LIST

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns

from app.core.slate_core import identify_entity
from app.core.slate_core import new_ahid
from app.core.slate_core import get_primid
from app.core.slate_core import list_primid_ahids
from app.core.slate_core import list_ahid_accounts
from app.core.slate_core import get_account_currency

from app.core.display import integer_to_money_format, integer_to_money_s_format

from app.core.flags import get_flag
from app.core.flags import delete_flag_key_from_map
from app.core.flags import set_flag, unset_flag

from app.core.payments import ah_payment

#==============================================================================
# The *robots* in this case are extremely simple agents, each identified by an
# *ahid* which (like any other) can be paired with an arbitrary set of
# *currencies*. The *robots* are identified by an additional column in the
# *ahids* table in one of the entities database files (entities_<PNSR>.db).
#
# The *robots* require some state information to be maintained and for this
# purpose have their own dedicated SQLite database (robots.db).
#
# When the "run_robots" flag is true, a number of actions occur:
#
# (1) When a payment is made by a human agent:
#
# If the payee *ahid* is identified as a *robot*, the payment is recorded in
# the "payments_received" table the primary key of which is an autoincremented
# integer "payment_id". The FPH of this robot *ahid* (the payee) is recorded
# along with the FPH of the payer *ahid* and that of the *currency*. (The
# annotation is discarded.) The payee *ahid* and the *currency* are then added
# to the list of known *currency*|*ahid* pairings if and only if not already
# listed.
#
# (2) A robot responds with a payment in the other direction:
#
# When the robot-management loop identifies the oldest payment received (if
# any) of the *ahid*, the sister *ahids* of that payee (i.e. those sharing the
# same *primid*) are then identified, and for each *ahid* in this expanded set
# the *currencies* paired with it are then identified. That payment record is
# then deleted from the queue.
#
# One of the possible *currency*|*ahid* pairings is selected at random from
# among these. A random-ly generated message (something inoffensive but
# realistic) is generated along with a randomly generated amount (something
# modest and appropriate for the message).
#
# By this approach, the human payer will receive a payment to one of its
# *currency*|*ahid* pairings from one of the *robots* known to it, in both
# cases selected at random.
#
# In this way, the human agent gets to experience an increasingly rich number
# of interactions (fairly realist apart from the quick response time).


#==============================================================================
# This database is created at installation time:
#
def create_robots_db():

    if os.path.exists(ROBOTS_DB):
        os.remove(ROBOTS_DB)

    with sqlite3.connect(ROBOTS_DB) as conn:
        cursor = conn.cursor()
        # Each payment received is added here, but is removed as soon as a
        # reponse payment has been made.
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS payments_received (" \
            + "payment_id INTEGER PRIMARY KEY AUTOINCREMENT, " \
            + "robot_fph TEXT NOT NULL, " \
            + "payer_ahid_fph TEXT NOT NULL, " \
            + "currency_fph TEXT NOT NULL " \
            + ");"
        )
        # This table lists the known *currency*|*ahid* pairings, each of which
        # is listed only once. When a response payment is made to one of these
        # pairings, the *ahid* determines the payee (since this is the *ahid*
        # from which a payment has recently been received).
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS known_pairings (" \
            + "pairing_id INTEGER PRIMARY KEY AUTOINCREMENT, " \
            + "robot_fph TEXT NOT NULL, " \
            + "ahid_fph TEXT NOT NULL, " \
            + "currency_fph TEXT NOT NULL " \
            + ");"
        )

        # NB:   robot_fph  is probably not needed
        #       pairing_id  may not be required

#==============================================================================


#number_of_robots = 100
#robot_parent = "sand.box.cc"

def create_robots(number_of_robots=10, robot_parent="sand.box.cc"):

#    print("Creating " + str(number_of_robots) + " robots in " + robot_parent)

    if number_of_robots < 10:
        d = 1
    elif number_of_robots < 100:
        d = 2
    elif number_of_robots < 1000:
        d = 3
    else:
        return False

    robots_list = []
    with open(ROBOTS_LIST, "w") as rl:
        for i in range(number_of_robots):
            name = "r" + str(i).zfill(d)
            ahid_fph, ahid_hrns, \
            m = new_ahid(name, robot_parent, "cc", robot=True)
            if m:
                print(m)
                continue
            print(name + " :: " + ahid_fph + " <> " + ahid_hrns)
            rl.write(ahid_hrns + "\n")

    return True


def get_next_robot_receipt():
    with sqlite3.connect(ROBOTS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT payment_id FROM payments_received")
        result = cursor.fetchall()
        if result is None: # no entries to process?
            cursor.close()
            return "", "", "", 0
        elif len(result) == 0:
            cursor.close()
            return "", "", "", 0
        elif len(result) == 1:
            next_in_queue = result[0][0]
        else:
            next_in_queue = min(result[0])
        still_in_queue = len(result) - 1
        cursor.execute(
            "SELECT robot_fph, payer_ahid_fph, currency_fph " \
            + "FROM payments_received WHERE payment_id = ?",
            (next_in_queue,)
        )
        result = cursor.fetchone()
        if result is None: # no entries to process?
            cursor.close()
            return "", "", "", still_in_queue
        payee_robot_fph = result[0]
        payer_ahid_fph = result[1]
        currency_fph = result[2]
        cursor.execute(
            "DELETE FROM payments_received WHERE payment_id = ?",
            (next_in_queue,)
        )
        cursor.close()
    return payee_robot_fph, payer_ahid_fph, currency_fph, still_in_queue


def send_next_robot_response():
    # Get the oldest message in the robot receipt queue. The following is the
    # robot to which a payment was sent:
    payer_ahid_fph, payee_robot_fph, currency_fph, \
    still_in_queue = get_next_robot_receipt()
    # Choose a robot from which to send a response payment:
    robots_list = []
    with open(ROBOTS_LIST, "r") as rl:
        robots = rl.readlines()
    for robot in robots:
        robots_list.append(robot.strip())
    responding_robot_hrns = random.choice(robots_list)
    responding_robot_fph, m = hrns_to_fph(responding_robot_hrns)
    # Now get the full list of *ahid*s to which a reply payment might be sent,
    # i.e. all the *ahid* belonging to the same *primid* as that from which the
    # robot was paid:
    payer_primid_fph, m = get_primid(payer_ahid_fph)
    payer_primid_ahids = list_primid_ahids(payer_primid_fph) # list
    pairing = {}
    # For each of the possible payee *ahid*s, identify the *currencies* with
    # which it is paired:
    for payee_ahid_fph in payer_primid_ahids:
        ahid_accounts_list, m = list_ahid_accounts(payee_ahid_fph)
        if m:
            print(m)
            continue
        currencies_list = []
        for account_fph in ahid_accounts_list:
            currency_fph, m = get_account_currency(account_fph)
            currencies_list.append(currency_fph)
        pairing[payee_ahid_fph] = currencies_list
    if len(payer_primid_ahids) > 0:
        reply_ahid_fph = random.choice(payer_primid_ahids)
        reply_currency_fph = random.choice(pairing[payee_ahid_fph])
        amount = random.randint(0, 999) * 100
#        message = "This payment has been sent by a robot selected at random " \
#                + "from among the robots currently using one of the " \
#                + "currencies in which you have an account. You, the payee, " \
#                + "have been selected at random from among the users of " \
#                + "that currency because you have already sent at least one " \
#                + "payment to one of the robots. The number of payments you " \
#                + "receive from robots will not exceed the number of " \
#                + "payments you send to robots."
        message = "From randomly-selected robot in randomly-selected currency."
        m = ah_payment(
                responding_robot_fph, reply_ahid_fph, reply_currency_fph,
                amount, message
            )
    return still_in_queue


def robots_respond():
    #print("cronned")
    while send_next_robot_response():
        time.sleep(0.2) # seconds
        if get_flag("run_robots"):
            continue # back to start of loop
        else:
            break

# When the "run_robots" flag is true, a number of

#set_flag("run_robots")

#thread = threading.Thread(target=robots_respond)
#thread.start()
