import sqlite3
import random
import os
import pickle
from string import ascii_lowercase
from datetime import datetime, date, time, timezone

from .slate_core import identify_entity

from .constants import MESSAGES_DB, DB_BKP_DIR

from .common import timestamp, unixtime_int

from .unix_functions import fcopy

#==============================================================================

def display_colour_subject_prefix(subject_prefix):
    category_colour = {}
    category_colour["payment received" : "#000040"]
    category_colour["offer" : "#008000"]
    category_colour["request" : "#408040"]
    category_colour["payment request" : "#400000"]
    category_colour["event" : "#FF8080"]
    category_colour["please respond" : "#4040F0"]
    category_colour["urgent" : "#800000"]
    category_colour["very_urgent" : "#A00000"]
    category_colour["final" : "#D00000"]
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
        subject_prefix,         # string
        subject,                # string
        longevity,              # integer: lifespan (seconds)
        expiry_datetime,        # string: YYYY-MM-DD_mm:ss
        message_body,           # string
        indelible = False,      # boolean
        expiry_timestamp = 0    # integer
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

    if not isinstance(subject_prefix, str):
        return "Invalid subject prefix string"

    category_colour = {}
    category_colour["payment received" : "#000040"]
    category_colour["offer" : "#008000"]
    category_colour["request" : "#408040"]
    category_colour["payment request" : "#400000"]
    category_colour["event" : "#FF8080"]
    category_colour["please respond" : "#4040F0"]
    category_colour["urgent" : "#800000"]
    category_colour["very_urgent" : "#A00000"]
    category_colour["final" : "#D00000"]
    category_colour.setdefault(" ", "#000000")

    if not isinstance(subject, str):
        return "Invalid subject string"

    if not isinstance(body, str):
        return "Invalid message body"

    try: # if the deletion date+time is valid
        deletion_scheduled = datetime.datetime(
                                 expiry_year, expiry_month, expiry_day,
                                 expiry_hour, expiry_minute, expiry_second
                             )
    except:
        if longevity: # if the deletion lifespan is valid
            if isinstance(longevity, int):
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
    recipient_fph, \
    recipient_hrns, \
    recipient_type, \
    m = identify_entity(recipient_identifier)

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
        if message_list is None:
            return 0, [] # no messages returned
#        message_count = 0
        timestamp_now = datetime.now(timezone.utc)
        deletions_due = []
        messages = [] # list of dictionaries
        for message in message_list:
            if message[2] < timestamp_now: # delete if due
                m = {}
                m["prefix_string"]
                m["rgb_colour"] = display_colour_subject_prefix(message[4])
                m["message_id"]         = message[0] # integer
                m["timestamp"]          = message[1] # integer
                m["expiry_timestamp"]   = message[2] # integer
                m["delete"]             = message[3] # boolean
                m["category"]           = message[4] # string
                m["prefix_string"]      = prefix_string # string
                m["rgb_colour"]         = rgb_colour # string
                m["indelible"]          = message[5] # boolean
                m["stewardship_hrns"]   = fph_to_hrns(message[6]) # string
                m["sender_hrns"]        = fph_to_hrns(message[7]) # string
                m["recipient_hrns"]     = fph_to_hrns(message[8]) # string
                m["subject"]            = message[9] # string
                m["message_body"]       = message[10] # string
                #
                # Can this message be displayed?
                if (m["timestamp"] <  m["expiry_timestamp"]) or m["indelible"]:
                    messages.append(m)
            else:
                cursor.execute(
                    "DELETE FROM messages WHERE message_id =?",
                    (message[0],)
                )
            conn.commit()
        cursor.close()



#            message_count += 1

#    return message_count, messages # list of dictionaries
    return messages # list of dictionaries


#==============================================================================
# Are any messages available?
#


def messages_available(recipient_identifier):
    recipient_fph, \
    recipient_hrns, \
    recipient_type, \
    m = identify_entity(recipient_identifier)

    with sqlite3.connect(MESSAGES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT message_id
            FROM messages
            WHERE recipient_fph = ?
            """,
            (recipient_fph,)
        )
        message_list = list(cursor.fetchall())
        if (message_list is None):
            cursor.close()
            return 0, 0 # no messages returned

        number_of_messages = len(message_list)
        # If the recipient is a *primid*, some messages may be indelible:
        if recipient_type != "primid":
            cursor.close()
            return number_of_messages, 0 # no indelible messages returned

        cursor.execute(
            """
            SELECT indelible
            FROM messages
            WHERE recipient_fph = ?
            """,
            (recipient_fph,)
        )
        indelible_message_list = list(cursor.fetchall())
        cursor.close()
    number_of_indelible_messages = len(indelible_message_list)
    if (indelible_message_list is None):
        return number_of_messages, 0 # no indelible messages found
    return number_of_messages, len(indelible_message_list)

#==============================================================================
# Are any messages available?
#
#def messages_available(identity):
#    messages = fetch_messages(identity)
#   return len(messages) > 0





# Delete all messages except those maeked indelible
#
def delete_all_messages(identity):


    return number_of_messages_deleted

# Delete all selected messages except those maeked indelible
#
def delete_selected_messages(identity, list_of_message_id):

    return number_of_messages_deleted

# Select messages from list:
#
def select_messages(identity, list_of_message_id):

    return number_of_messages_selected
