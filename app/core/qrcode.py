import pyqrcode
import os
import datetime

from app.core.slate_core import random_filename
from app.core.slate_core import identify_entity
from app.core.slate_core import get_config

from app.core.common import unixtime_int

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


def qr_code_png(url, qr_png_name):
    # A QR code PNG is generated for the URL provided:
    # The PNG is saved in the common QR code directory:
    png_path = QR_CODES + random_filename() + ".png"
    qr_url = pyqrcode.create(url)
    qr_url.png(png_path, scale = 8)
    return png_path # for display/deletion


def qrencode_invitation(currency_id, namespace_id, inviter_id):
    currency_fph, currency_hrns, etype, m = identify_entity(currency_id)
    namespace_fph, namespace_hrns, etype, m = identify_entity(namespace_id)
    inviter_fph, inviter_hrns, etype, m = identify_entity(inviter_id)
    #time_now = unixtime_int() # nanosecond precision
    config = get_config()
    if "qr_lifespan" in config.keys():
        qr_lifespan = int(config["qr_lifespan"]) # seconds
    else:
        qr_lifespan = 60
    if "hub_url" in config.keys():
        hub_url = config["hub_url"]
    else:
        return ""
    qr_expiry_time = str(unixtime_int() + qr_lifespan*1000000000)
    deathtime = str(qr_expiry_time) # for use in filename
    # URL of the website for which we are making QR code
    s = hub_url + "/register" \
      + "?c=" + currency_fph \
      + "&s=" + namespace_fph \
      + "&f=" + inviter_fph \
      + "&e=" + qr_expiry_time # after which the QR code becomes invalid
    qr_png_filename = deathtime + "_" + random_filename() + ".png"
    qr_png_path = QR_CODES + qr_png_filename
    qr_url = pyqrcode.create(s)
    qr_url.png(qr_png_path, scale = 6)
    return qr_png_filename


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
