import sqlite3
import random
import os
import pickle
from string import ascii_lowercase
from datetime import datetime, date, time, timezone
import calendar

from app.core.slate_core import identify_entity
from app.core.slate_core import account_status
from app.core.slate_core import list_secids, list_ahids
from app.core.slate_core import get_ahid_primid, get_primid

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns

from app.core.constants import MESSAGES_DB, DB_BKP_DIR

from app.core.common import filename_timestamp as timestamp
from app.core.common import unixtime_int, unixtime_str

from app.core.display import integer_to_money_s_format

from app.core.unix_functions import fcopy

from app.core.regexp_list import re_datestamp

from app.core.logging import log_event

#==============================================================================

#def display_colour_subject_prefix(subject_prefix):
def category_display_colour(subject_prefix):
    category_colour = {}
    category_colour["payment received"] = "#000040"
    category_colour["offer"] = "#008000"
    category_colour["request"] = "#408040"
    category_colour["payment"] = "#400000"
    category_colour["payment_request"] = "#400000"
    category_colour["event"] = "#FF8080"
    category_colour["please respond"] = "#4040F0"
    category_colour["urgent"] = "#800000"
    category_colour["very_urgent"] = "#A00000"
    category_colour["final"] = "#D00000"
    category_colour.setdefault(" ", "#000000")
    return category_colour[subject_prefix]

#==============================================================================
#

def create_messages_db():

    # This database is used to hold short structured (JSON) messages
    # - *agent* to *agent*      one-to-one
    # - stewards to *agent*     many-via-one-to-one
    # - *agent* to stewards     one-to-many-via-one
    # which are to be displayed sequentially in a user's login landing screen
    # and, once read, either
    # - deleted from the database
    # or
    # - archived for later retrieval

    if os.path.exists(MESSAGES_DB):
        # If the database exists already, it is deleted after a time-stamped
        # copy has been saved.
        fcopy(MESSAGES_DB, DB_BKP_DIR + '/messages_' + timestamp() + '.db')
        os.remove(MESSAGES_DB)

    with sqlite3.connect(MESSAGES_DB) as conn:
        cursor = conn.cursor()
        # The initial values for the following details are read from a
        # configuration file at the time of installation.
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                expiry_timestamp TEXT,
                deletion_scheduled INTEGER DEFAULT 0,
                category INTEGER DEFAULT 0,
                indelible INTEGER DEFAULT 0,
                stewardship_fph TEXT,
                sender_fph TEXT,
                recipient_identity_fph TEXT,
                recipient_primid_fph TEXT,
                payer_account_fph TEXT,
                payee_account_fph TEXT,
                payer_ahid_fph TEXT,
                payee_ahid_fph TEXT,
                currency_fph TEXT,
                amount INTEGER,
                subject TEXT,
                message_body TEXT
            );
            """
        )

    # Fields:
    #
    #   message_id          Unique message identifier (*auto-incremented) which
    #                       simplifies deletion by authorized *agent* (usually
    #                       a steward or a house-keeping process).
    #
    #   timestamp           The date+time at which this message was sent.
    #
    #   expiry_timestamp    If set, the message will disappear at or soon after
    #                       this date+time.
    #
    #   deletion_scheduled  If true, this message has already been scheduled for
    #                       deletion.
    #
    #   category            0: standard message         display: black
    #                       1: offer                    display: green
    #                       2: request                  display: brown
    #                       3: event notification       display: orange-brown ?
    #                       4: please respond           display: grey-blue
    #                       5: urgent                   display: red
    #                       6: very_urgent              display: red
    #                       7: final                    display: red
    #
    #                       If >= 4, the recipient cannot delete the message
    #                       although the sender can.
    #
    #   indelible           If TRUE, the recipient cannot delete the message
    #                       although the send can.
    #
    #   stewardship_id      If the message has been sent by a steward, this (as
    #                       FPH or HRNS) identifies the *namespace* or
    #                       *currency* of which the sender_id is one of the
    #                       stewards.
    #
    #                       If the message has been sent to the stewards of a
    #                       *namespace* or *currency*, this identifies (as
    #                       FPH or HRNS) the entity.
    #
    #   sender_fph          The *agent* who sent this message.
    #
    #   recipient_fph       The *agent* to whom this message has been sent.
    #                       This may be a *primid*, a *secid* or an *ahid*.
    #
    #   subject             The subject line, displayed with the prefix string
    #                       and in the colour appriate to the message category.
    #
    #   message_body        Brevity is a virtue.

    return

#==============================================================================
#

def send_message(
        message_timestamp,
        sender_identifier,      # FPH or HRNS - *primid*, *secid* or *ahid*
        recipient_identifier,   # FPH or HRNS - *primid*, *secid* or *ahid*
        category,               # string
        subject_prefix,         # string
        subject,                # string
        stewardship_id,         # entity FPH or HRNS
        longevity,              # integer: lifespan (seconds)
        expiry_datetime,        # string: YYYY-MM-DD_mm:ss
        payer_account_fph,      # used in all modes other than "omtrad"
        payee_account_fph,      # used in all modes other than "omtrad"
        payer_ahid_fph,         # used in "omtrad" mode
        payee_ahid_fph,         # used in "omtrad" mode
        currency_fph,           # string
        amount,                 # integer
        message_body,           # string
        indelible = False       # boolean
    ):

#    print()
#    print(message_timestamp)
#    print("from: " + fph_to_hrns(sender_identifier))
#    print("to: " + fph_to_hrns(recipient_identifier))
#    print("category: " + category)
#    if subject_prefix:
#        print(subject_prefix)
#    print(subject)
#    if stewardship_id:
#        print(stewardship_id)
#    if longevity:
#        print(longevity)
#    if expiry_datetime:
#        print(expiry_datetime)
#    if payer_account_fph:
#        print(fph_to_hrns(payer_account_fph))
#    if payee_account_fph:
#        print(fph_to_hrns(payee_account_fph))
#    if payer_ahid_fph:
#        print(fph_to_hrns(payer_ahid_fph))
#    if payee_ahid_fph:
#        print(fph_to_hrns(payee_ahid_fph))
#    if currency_fph:
#        print(fph_to_hrns(currency_fph))
#    if amount:
#        print(amount)
#    print(message_body)
#    print(indelible)
#    print()


    sender_fph, \
    sender_hrns, \
    etype, \
    em = identify_entity(sender_identifier)
    if em:
        return "Sender unknown"

    recipient_identity_fph, \
    recipient_identity_hrns, \
    etype, \
    em = identify_entity(recipient_identifier)
    if em:
        return "Recipient unknown"

    recipient_primid_fph, m = get_primid(recipient_identity_fph)



    if stewardship_id:
        stewardship_fph, \
        stewardship_hrns, \
        etype, \
        em = identify_entity(stewardship_id)
    else:
        stewardship_fph = ""
        stewardship_hrns = ""
        etype = ""

    if not isinstance(subject_prefix, str):
        return "Invalid subject prefix string"

    if not isinstance(subject, str):
        return "Invalid subject string"

#    subject = subject_prefix + ": " + subject
    if subject_prefix:
        subject = subject_prefix + ": " + subject

    if not isinstance(message_body, str):
        return "Invalid message body"

    timestamp_now = datetime.now(timezone.utc)

    #print("message_timestamp = " + str(message_timestamp))
#    print("message_timestamp = " +  message_timestamp)

    if expiry_datetime: # no expiry if ""
        if not re_datestamp.match(expiry_datetime):
            return "Invalid expiry date and time"
        else:
            expiry_dt = expiry_datetime.split("_")
            expiry_date = expiry_dt[0]
            expiry_time = expiry_dt[1]
            expiry_d = expiry_date.split("-")
            expiry_year = expiry_d[0]
            expiry_month = expiry_d[1]
            expiry_day = expiry_d[2]
            expiry_t = expiry_time.split(":")
            expiry_hour = expiry_t[0]
            expiry_minute = expiry_t[1]
            expiry_second = expiry_t[2]

            try: # if the deletion date+time is valid
                deletion_scheduled = datetime.datetime(
                                         expiry_year, expiry_month, expiry_day,
                                         expiry_hour, expiry_minute,
                                         expiry_second
                                     )
            except:
                if longevity: # if the deletion lifespan is valid
                    if isinstance(longevity, int):
                        deletion_scheduled = int(unixtime_int() > longevity)
                        #deletion_scheduled = longevity + timestamp_now
                                           #+ datetime.now(timezone.utc)
                    else:
                        deletion_scheduled = 0 # not scheduled for deletion
    else:
        deletion_scheduled = 0 # not scheduled for deletion

    with sqlite3.connect(MESSAGES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO messages (
                timestamp,
                expiry_timestamp,
                deletion_scheduled,
                category,
                indelible,
                stewardship_fph,
                sender_fph,
                recipient_identity_fph,
                recipient_primid_fph,
                payer_account_fph,
                payee_account_fph,
                payer_ahid_fph,
                payee_ahid_fph,
                currency_fph,
                amount,
                subject,
                message_body
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_timestamp,
                expiry_datetime,
                deletion_scheduled,
                category,
                indelible,
                stewardship_fph,
                sender_fph,
                recipient_identity_fph,
                recipient_primid_fph,
                payer_account_fph,
                payee_account_fph,
                payer_ahid_fph,
                payee_ahid_fph,
                currency_fph,
                amount,
                subject,
                message_body
            )
        )
        conn.commit()
        cursor.close()

    return ""

#==============================================================================
#

def fetch_messages(recipient_identifier):

    recipient_fph, \
    recipient_hrns, \
    recipient_type, \
    em = identify_entity(recipient_identifier)

#    print(recipient_hrns)

    with sqlite3.connect(MESSAGES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                message_id,
                timestamp,
                expiry_timestamp,
                deletion_scheduled,
                category,
                indelible,
                stewardship_fph,
                sender_fph,
                recipient_identity_fph,
                recipient_primid_fph,
                payer_account_fph,
                payee_account_fph,
                payer_ahid_fph,
                payee_ahid_fph,
                currency_fph,
                amount,
                subject,
                message_body
            FROM messages
            WHERE recipient_identity_fph = ?
            """,
            (recipient_fph,)
        )
        message_list = list(cursor.fetchall())
        if message_list is None:
            return 0, [] # no messages returned
        timestamp_now = datetime.now(timezone.utc)
        deletions_due = []
        messages = [] # list of dictionaries
        for message in message_list:

#            print(message)

            message_id = message[0]
            timestamp = message[1]
            expiry_timestamp = message[2]
            delete = bool(message[3])
            category = message[4]
            indelible = bool(message[5])
            stewardship_fph = message[6]
            sender_fph = message[7]
            recipient_identity_fph = message[8]
            recipient_primid_fph = message[9]
            payer_account_fph = message[10]
            payee_account_fph = message[11]
            payer_ahid_fph = message[12]
            payee_ahid_fph = message[13]
            currency_fph = message[14]
            amount = message[15]
            subject = message[16]
            message_body = message[17]
            if expiry_timestamp:
                ets = message[2].split("_")
                ed = ets[0].split("-")
                et = ets[1].split(":")
                year = int(ed[0])
                month = int(ed[1])
                day = int(ed[2])
                hour = int(et[0])
                minute = int(et[1])
                second = int(et[2])
                eds = datetime(year, month, day, hour, minute, second)
                expiry_timestamp = calendar.timegm(eds.timetuple())
            else:
                expiry_timestamp = 0
            # Display if indelible deletion not due
            if (expiry_timestamp < unixtime_int()) or indelible:
                m = {}
                m["rgb_colour"] = category_display_colour(message[4])
                m["message_id"] = message_id # integer
                m["timestamp"] = timestamp # integer
                m["expiry_timestamp"] = expiry_timestamp #
                m["delete"] = delete     # boolean
                m["category"] = category # string
                m["indelible"] = indelible  # boolean
                m["stewardship_fph"] = stewardship_fph
                m["stewardship_hrns"] = fph_to_hrns(stewardship_fph) # string
                m["sender_fph"] = sender_fph
                m["sender_hrns"] = fph_to_hrns(sender_fph) # string
                m["recipient_fph"] = recipient_fph
                m["recipient_hrns"] = fph_to_hrns(recipient_fph) # string
                if payer_ahid_fph:
                    m["payer_hrns"] = fph_to_hrns(payer_ahid_fph)
                elif payer_account_fph:
                    m["payer_account_hrns"] = fph_to_hrns(payer_account_fph)
                if payee_ahid_fph:
                    m["payee_hrns"] = fph_to_hrns(payee_ahid_fph)
                elif payee_account_fph:
                    m["payee_account_hrns"] = fph_to_hrns(payee_account_fph)
#                payer_account_exists, \
#                payer_account_active, \
#                payer_account_currency_fph, \
#                payer_account_owner_fph, \
#                payer_account_ahid_fph, \
#                payer_account_balance, \
#                payer_account_volume, \
#                em = account_status(payer_account_fph)
#                m["payer_identity_hrns"] = fph_to_hrns(payer_account_owner_fph)
#                m["payee_account_fph"] = payee_account_fph
#                if payee_account_fph: # may be blank
#                    m["payee_account_hrns"] = fph_to_hrns(payee_account_fph)
#                payee_account_exists, \
#                payee_account_active, \
#                payee_account_currency_fph, \
#                payee_account_owner_fph, \
#                payee_account_ahid_fph, \
#                payee_account_balance, \
#                payee_account_volume, \
#                em = account_status(payee_account_fph)
#                m["payee_identity_hrns"] = fph_to_hrns(payer_account_owner_fph)
                if currency_fph:
                    m["currency_hrns"] = fph_to_hrns(currency_fph)
#                    print("Groucho")
#                else:
#                    continue    # omit this message from list returned (should
                                # never happen)

                if isinstance(amount, int):
                    m["amount"] = integer_to_money_s_format(amount)
                else:
                    m["amount"] = ""

                m["subject"] = subject # string

                m["message_body"] = message_body # string
                #messages.append(m)
                messages.insert(0, m)

                #print(m)

            elif expiry_timestamp: # delete only if expiry_timestamp is set
                cursor.execute(
                    "DELETE FROM messages WHERE message_id = ?",
                    (message[0],)
                )
            conn.commit()
        cursor.close()

    return messages # list of dictionaries


#==============================================================================
# Get the number of messages available for this *primid*.
# If in "omtrad" mode, include thos for *ahid*s.
# Otherwise, include those for *secids*.
#
def message_count(primid_id, hub_mode):

    primid_fph, \
    primid_hrns, \
    etypes, \
    m = identify_entity(primid_id)
    if m:
        log_event(
            "error",
            "primid unidentified",
            "Entity " + primid_id + " is not registered"
        )
        print(m)
        return 0, 0
    elif primid_fph == "":
        log_event(
            "error",
            "primid unidentified",
            "Entity " + primid_id + " is not registered"
        )
        return 0, 0
    elif not ("primid" in etypes):
        log_event(
            "error",
            "primid not registered",
            "No primid is registered for " + primid_hrns
        )
        return 0, 0


    if hub_mode == "omtrad":
        recipient_list = list_ahids(primid_fph)
    else:
        recipient_list = list_secids(primid_fph)
    recipient_list.append(primid_fph)
    #print(recipient_list)
#    for recipient_fph in recipient_list:
#        print(fph_to_hrns(recipient_fph))

    number_of_messages = 0
    #number_of_indelible_messages = 0
    with sqlite3.connect(MESSAGES_DB) as conn:
        cursor = conn.cursor()
        for recipient_fph in recipient_list:
#            print(fph_to_hrns(recipient_fph))
            cursor.execute(
                """
                SELECT message_id
                FROM messages
                WHERE recipient_primid_fph = ?
                """,
                (primid_fph,)
            )
        message_id_list = list(cursor.fetchall())
        if message_id_list is None:
            cursor.close()
            return 0, 0 # no messages returned
        number_of_messages += len(message_id_list)
        cursor.execute(
            """
            SELECT indelible
            FROM messages
            WHERE recipient_primid_fph = ? AND indelible = 1
            """,
            (primid_fph,)
        )
        indelible_message_list = list(cursor.fetchall())
        cursor.close()
    if indelible_message_list is None:
        return number_of_messages, 0 # no indelible messages found
    else:
#        print("messages: " + str(number_of_messages))
#        print("indelible messages: " + str(len(indelible_message_list)))
        return number_of_messages, len(indelible_message_list)


#==============================================================================
# Are any messages available for the specified recipient?
#
def messages_available(recipient_identifier):

    recipient_fph, \
    recipient_hrns, \
    recipient_type, \
    em = identify_entity(recipient_identifier)

#    print("recipient_fph = " + recipient_fph)
#    print("recipient_hrns = " + recipient_hrns)

    with sqlite3.connect(MESSAGES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT message_id
            FROM messages
            WHERE recipient_identity_fph = ?
            """,
            (recipient_fph,)
        )
        #message_list = list(cursor.fetchall())
        message_id_list = list(cursor.fetchall())
        if message_id_list is None:
            cursor.close()
            return 0, 0 # no messages returned
#        print(message_id_list)

        number_of_messages = len(message_id_list)
#        print(
#            recipient_hrns + " has received "
#            + str(number_of_messages) + " messages"
#        )

        # If the recipient is a *primid*, some messages may be indelible:
        if recipient_type != "primid":
            return number_of_messages, 0
        cursor.execute(
            """
            SELECT indelible
            FROM messages
            WHERE recipient_identity_fph = ? AND indelible = 1
            """,
            (recipient_fph,)
        )
        indelible_message_list = list(cursor.fetchall())
        cursor.close()
        if indelible_message_list is None:
            return number_of_messages, 0 # no indelible messages found
        else:
            return number_of_messages, len(indelible_message_list)








#==============================================================================
# Are any messages available?
#
#def messages_available(identity):
#    messages = fetch_messages(identity)
#   return len(messages) > 0


def delete_message(message_id):

    if not isinstance(message_id, str):
        return "message_id is not a string"
    elif not message_id.isdigit():
        return "message_id is not an integer"

    with sqlite3.connect(MESSAGES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM messages WHERE message_id = ?",
            (int(message_id),)
        )
        conn.commit()
        cursor.close()

    return ""




# Delete all messages except those maeked indelible
#
def delete_all_messages(recipient_fph):

    with sqlite3.connect(MESSAGES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM messages WHERE recipient_identity_fph = ?",
            (recipient_fph,)
        )
        conn.commit()
        cursor.close()

    return

# Delete all selected messages except those maeked indelible
#
def delete_selected_messages(identity, list_of_message_id):

    return number_of_messages_deleted

# Select messages from list:
#
def select_messages(identity, list_of_message_id):

    return number_of_messages_selected
