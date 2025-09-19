import sqlite3
#import random
import os
import time
import threading
import multiprocessing
#import names

from app.core.constants import ROBOTS_DB
from app.core.constants import ROBOTS_LIST

from app.core.slate_core import identify_entity
from app.core.slate_core import new_ahid

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

    for i in range(number_of_robots):
        name = "r" + str(i).zfill(d)
        print(name, end="")
        ahid_fph, ahid_hrns, m = new_ahid(name, robot_parent, "cc", robot=True)
        print(" :: " + ahid_fph + " <> " + ahid_hrns)
        robots_list.append(ahid_hrns)

    with open(ROBOTS_LIST, "w") as rl:
        for ahid_hrns in robots_list:
            rl.write(ahid_hrns)

    return True

# Each time a new *currency* is created it will paired with each of the robots.
# Therefore the number of robots is kept low.

#def create_robot_pairing(ahid_fph, currency_fph):
#
#    with sqlite3.connect(ROBOTS_DB) as conn:
#        cursor = conn.cursor()
#        cursor.execute(
#            "SELECT ahid_fph, currency_fph FROM known_pairings",
#            (ahid_fph, currency_fph)
#        )
#        result = cursor.fetchone()
#        cursor.close()
#    if result is None: # the pairing does not yest exist
#        account_fph, account_hrns, \
#        m = new_pairing("cc", ahid_fph, currency_fph)





# When the "run_robots" flag is true, a number of

def get_next_received_payment_pairing():
    with sqlite3.connect(ROBOTS_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT payment_id FROM payments_received")
        result = cursor.fetchall()
        if result is None: # no entries to process?
            cursor.close()
            return "", "", ""
        next_in_queue = min(result[0])
        cursor.execute(
            "SELECT payment_id, robot_fph, payer_ahid_fph " \
            + "FROM payments_received WHERE payment_id = ?",
            (next_in_queue,)
        )
        result = cursor.fetchone()
        payee_robot_fph = result[0]
        payer_ahid_fph = result[1]
        currency_fph = result[2]
        cursor.execute(
            "DELETE FROM payments_received WHERE payment_id = ?",
            (next_in_queue,)
        )
        cursor.close()
    return robot_fph, ahid_fph, currency_fph



def robots_loop():

    while get_flag("run_robots"):
        time.sleep(1.0) # seconds

        payee_robot_fph, \
        payer_ahid_fph, \
        currency_fph = get_next_received_payment_pairing()
        if not robot_fph:
            continue # back to start of loop

        # Now get the full list of *ahid*s to which a "reply" payment might be
        # sent:
        payer_primid_fph = get_primid(payer_ahid_fph)
        payer_primid_ahids = get_ahids(payer_primid_fph) # list
        pairing = {}
        for payee_ahid in payer_primid_ahids:
            pairing[payee_ahid] = get_currencies(payee_ahid)
        reply_ahid = fph_to_hrns(random.choice(payer_primid_ahids))
        reply_currency = fph_to_hrns(random.choice(pairing[payee_ahid]))

        amount = random.randint()
        message = "The medium is the massage"

        m = ah_payment(
                payer_ahid_hrns,
                payee_ahid_hrns,
                currency_hrns,
                amount,
                message
            )





#thread = threading.Thread(target=worker)
#thread.start()
