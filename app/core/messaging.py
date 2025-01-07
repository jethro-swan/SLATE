import sqlite3
import random
import os
import pickle
from string import ascii_lowercase
import datetime
import time

from .constants import MESSAGES_DB

from .common import timestamp, unixtime_int

#==============================================================================

def display_colour_subject_prefix(message_category):
    prefix = []
    colour = []
    prefix.append("")
    colour.append("#000000")
    prefix.append("offer")
    colour.append("#008000")
    prefix.append("request")
    colour.append("#408040")
    prefix.append("event notification")
    colour.append("FF8080")
    prefix.append("please respond")
    colour.append("4040F0")
    prefix.append("urgent")
    colour.append("#800000")
    prefix.append("very_urgent")
    colour.append("#A00000")
    prefix.append("final")
    colour.append("#D00000")
    prefix_string = prefix[message_category]
    rgb_colour = colour[message_category]
    return prefix_string, rgb_colour

#==============================================================================
#

def create_hubs_db():

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
    #
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
                stewardship_id TEXT,
                sender_fph TEXT,
                recipient_fph TEXT,
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
    #
    #   subject             The subject line, displayed with the prefix string
    #                       and in the colour appriate to the message category.
    #
    #   message_body        Brevity is a virtue.

    return

#==============================================================================
#

def send_message(
        sender_identifier,      # FPH or HRNS
        recipient_identifier,   # FPH or HRNS
        subject,                # text
        longevity,              # lifespan (seconds)
        expiry_year,    #
        expiry_month,   ######### date+time for scheduled removal
        expiry_day,     #
        expiry_hour,    #       Values entered in form validated on submission
        expiry_minute,  #
        expiry_second,  #
        message_body,           # text
        indelible = False,      # boolean
        expiry_timestamp = "",  # text
    ):

    sender_fph, \
    sender_hrns, \
    etype, \
    m = identify_entity(sender_identifier)
    if m:
        return "Sender unknown"

    recipient_fph, \
    recipient_hrns, \
    etype, \
    m = identify_entity(recipient_identifier)
    if m:
        return "Recipient unknown"

    if isinstance(subject, str):
        return "Invalid subject string"

    if isinstance(body, str):
        return "Invalid message body"

    try: # if the deletion date+time is valid
        deletion_scheduled = datetime.datetime(
                                 expiry_year, expiry_month, expiry_day,
                                 expiry_hour, expiry_minute, expiry_second
                             )
    except:
        if longevity: # if the deletion lifespan is valid
            if isinstance(longevity, int)
                deletion_scheduled = longevity + datetime.now(timezone.utc)
        else:
            deletion_scheduled = 0 # not sceduled for deletion

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
                stewardship_id,
                sender_fph,
                recipient_fph,
                subject,
                message_body
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                timestamp,
                expiry_timestamp,
                deletion_scheduled,
                category,
                indelible,
                stewardship_id,
                sender_fph,
                recipient_fph,
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
                stewardship_id,
                sender_fph,
                recipient_fph,
                subject,
                message_body
            FROM messages
            WHERE recipient_fph = ?
            """,
            (recipient_fph,)
        )
        message_list = list(cursor.fetchall())
#        cursor.close()
        if result is None:
            return 0, [] # no messages returned
#        message_count = 0
        timestamp_now = datetime.now(timezone.utc)
        deletions_due = []
        messages = [] # list of dictionaries
        for message in message_list:
            if message[2] < timestamp_now: # delete if due
                m = {}
                m["message_id"]         = message[0]
                m["timestamp"]          = message[1]
                m["expiry_timestamp"]   = message[2]
                m["deletion_scheduled"] = message[3]
                m["category"]           = message[4]
                m["indelible"]          = message[5]
                m["stewardship_id"]     = message[6]
                m["sender_fph"]         = message[7]
                m["recipient_fph"]      = message[8]
                m["subject"]            = message[9]
                m["message_body"]       = message[10]
                messages.append(m)
            else:
                cursor.execute(
                    "DELETE FROM messages WHERE message_id =?",
                    (message[0],)
                )
            )
            conn.commit()
        cursor.close()



#            message_count += 1

#    return message_count, messages # list of dictionaries
    return messages # list of dictionaries

#==============================================================================
