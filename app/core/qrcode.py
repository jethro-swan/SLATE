#!/usr/bin/env python3

import pyqrcode
#import xxhash
#from xxhash import xxh32
import os
import datetime

from app.core.constants import QR_CODES

# QR code applications:
#
# 1. Invitation to register for use of a specific currency:
#
#       Displayed on:
#           printed sheet or card displayed by vendor already using currency
#           web page of vendor already using currency
#           other printed material authorized by currency's steward(s)
#           other web presence authorized  by currency's steward(s)
#
#       May be:
#           restricted
#               geographically
#               temporally
#                   expiry
#                   times of day
#                   days of week
#               by usage (as defined by the currency's steward(s))
#
#       Encodes:
#           hub (URL)
#           currency (with full namespace path)
#           restrictions
#
#       Takes user scanning invitation QR code to:
#           registration page on hub
#               displaying
#                   currency name
#                   namespace path
#                   currency properties/purpose/description
#               inviting user to enter
#                   * user name
#                   * password (provide autogeneration option)
#                   public key
#                   email address (for password replacement)
#                   mobile number (for password replacement)
#               generating QR coded page (printable) to enable
#                   quick login by scanning QR code
#
#       Saves:
#           username
#               (creates new namespace directory)
#           password hash
#           public key
#           contact/recovery information
#               email address
#               mobile number
#           name (required for merchants)
#           address (required for merchants)
#           other business details (required for merchants)
#           QR code uniquely identifying the user and encoding relevant data




#
# 2. Confirm payment when requested:
#
#       The simplest approach may be to ask the buyer to scan a fixed printed
#       QR code displayed by the vendor's counter. This QR code would uniquely
#       identify the seller (and possibly the location) along with the
#       seller's account and the currency.
#
#       On scanning the QR code (using a handheld device, most probably a
#       phone) the buyer would be taken to web page displaying
#           the vendor name (and possibly the location)
#           the currency name (possibly including the full namespace path)
#           the amount (and unit)
#           the date and time
#       inviting the buyer to
#           confirm the transaction (button - touch or click)
#       and offering the buyer the option to
#           have receipt emailed (iff the buyer has registered address)
#           have receipt sent as SMS (if the buyer has register number)

#
#
#
#
#       Displayed on:
#           vendor web page
#               checkout
#                   addendum to legal tender payment
#
#           vendor PoS device - be
#
#
#       Encodes:
#           hub (URL)
#           currency (full namespace path)
#           payer account (full namespace path)
#           payee account (full namespace path)
#           amount (and units)
#           unique transaction code comprising
#               date+time (YYYYMMDDhhmm)
#               hash of random number
#
#       Takes user scanning QR code to:
#           confirmation page on hub
#               displaying
#                   currency (local | full namespace path)
#                   amount (transaction number)
#               providing
#                   button (click/touch) to confirm transaction
#
# For later use with NESTS Flask interface:
#



# For later use with NESTS Flask interface:


def random_name():
    # A random name is generated for the QR code:
    timestamp_format = "%Y%m%d%H%M%S%f"   # YYYYMMDDhhmmss...... (20 digits)
    timestamp20 = datetime.datetime.now().strftime(timestamp_format)
    ##random32 = xxh32(str(random.randrange(0, 9999999999)).strip()).hexdigest()
    # Return a 52-character string comprising the date and time of generation
    # terminated by a random string:
    return timestamp20 + random32

def qr_code_png(url, qr_png_name):
    # A QR code PNG is generated for the URL provided:
    # The PNG is saved in the common QR code directory:
#    png_path = QR_CODES + \
    png_name = qr_png_name \
             + datetime.datetime.now().strftime("%Y%m%d%H%M%S%f") \
             + ".png"
    qr_url = pyqrcode.create(url)
    qr_url.png(png_path, scale = 8)
    return png_name # for display





def qrencode_invitation(
#        get_config("hub_url"),
        currency_fph,
        namespace_fph,
        inviter_fph,
        expiry # Unix time
    ):
    # URL of the website for which we are making QR code
    s = get_config("hub_url") \
      + "&c=" + currency_fph \
      + "&s=" + namespace_fph \
      + "&f=" + inviter_fph \
      + "&e=" + expiry # Unix time
#    qr_png_name = currency_fph + '_' + inviter_fph + '_'
    qr_png_name = random_name()
    return qr_code_png(s, qr_png_name)
    #qr_png_path = qr_code_png(s, qr_png_name)
    #return qr_png_path

#def qrencode_payment(hub, currency_fph, payer_fph, payee_fph, amount, transid):
def qrencode_payment(hub, payer_fph, payee_fph, amount):
    s = get_config("hub_url") \
      + "&f=" + payer_fph \
      + "&t=" + payee_fph \
      + "&a=" + amount
    qr_png_name = payer_fph + '_' \
                + payee_fph + '_' \
                + transid + '_'
    return qr_code_png(s, qr_png_name)
    #qr_png_path = qr_code_png(s, qr_png_name)
    #return qr_png_path
