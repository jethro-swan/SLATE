# Last modified: 2023-08-28 20.45 JW

import bcrypt
import re
import secrets
import string
import random
import sys
import json
import os
import sys
import sqlite3
#import logging

from .dbm_functions import dbm_store, dbm_fetch, dbm_delete
from .regexp_list import re_email
from .common import nshash
from .logging import log_event

#------------------------------------------------------------------------------
# Used to authenticate both passwords and recovery details (email addresses or
# phone numbers).

def auth_hash(password):
    hash_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")

def check_auth_hash(password, pwd_hash):
#    return bcrypt.checkpw(password.encode("utf-8"), pwd_hash.encode("utf-8"))
    try:
        password_authenticated = bcrypt.checkpw(
                                            password.encode("utf-8"),
                                            pwd_hash.encode("utf-8")
                                        )
    except Exception as exception:
        #logging.exception('') # using Python logging module
        log_event("errors", "auth_hash( _)", exception)
        print(exception)
        return False
    else:
        return password_authenticated






#def authenticate_cli_access(fph, auth_code):
#    properties = get_properties(fph)
#    pwd_hash_decoded = properties["auth"]["cli_password_hash"].decode("utf-8")
#    return check_auth_hash(auth_code, pwd_hash_decoded)

# (1) For "normal" passwords:

#exclusion_list = "\"\'"
nonalnum_characters = "!#$%&()*+,-./:;<=>?@[\]^_`{|}~"

def list_password_characters():
    return "The password may contain the following characters:\n" \
           + "   upper case letters\n" \
           + "   lower case letters\n" \
           + "   numbers\n" \
           + "   !#$%&()*+,-./:;<=>?@[\]^_`{|}~\n" \
           + "and must contain at least one of each type."  \
           + "It must be at least 16 characters in length."

# Regular expression to validate such a password:
pwd_regexp = r"((?=.*\d)(?=.*[a-z])(?=.*[A-Z])" \
           + r"(?=.*[!#$%&()*+,-./:;<=>?@[\]^_`{|}~]).{16,})"
re_pwd = re.compile(pwd_regexp)

def password_valid(password):
    return re_pwd.match(password)

# Generate password of at least 16 characters:
def generate_password(min_length):
    if min_length < 16:
        min_length = 16
    max_length = 32
    pwd_length = random.randint(min_length, max_length)
    n_pchars = random.randint(2, 5)
    n_digits = random.randint(2, 5)
    n_alphac = min_length - n_pchars - n_digits
    valid_chars = string.ascii_letters \
                + string.digits \
                + "!#$%&()*+,-./:;<=>?@[\]^_`{|}~"
    pwd = []
    for i in range(pwd_length):
        pwd.append(random.choice(valid_chars))
    return "".join(pwd)



# (2) For "URL-safe" passwords:

def list_url_safe_password_characters():
    return "The password may contain the following characters:\n" \
           + "   upper case letters\n" \
           + "   lower case letters\n" \
           + "   numbers\n" \
           + "   '-' or '_'\n" \
           + "and must contain at least one of each type.\n" \
           + "It must be at least 16 characters in length."

# Regular expression to validate such a password:
re_urls_pwd = re.compile(r"((?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[_-]).{16,})")

def url_safe_password_valid(password):
    return re_urls_pwd.match(password)

# Generate URL-safe password of at least 16 characters:
def generate_url_safe_password(n):
    if n < 16:
        n = 16
    pw = secrets.token_urlsafe(n)
    while not password_valid(pw):
        pw = secrets.token_urlsafe(n)
    return pw



#------------------------------------------------------------------------------
# Generate an access toke:
def generate_access_token():
    # An access token is generated:
    ri = random.randint(0,9999999)
    return nshash(str(random.randint(0,ri)*random.randint(0,9999999)))

# This is used mainly for command line (over SSH) access.




#------------------------------------------------------------------------------
# Content of primary identity .auth file:
json_auth_tpl   =   {
                        "CLI_auth_hash": "",    # duplicated in .auth file
                        "web_password_hash": "",
                        "PIN": "",              # 6-digit PIN for SWI access.
                        "SSL_pubkey": [""]      # Any number of keys. Searched
                                                # in sequence until a valid
                                                # entry is found.
                    }

## The following function definitions have been recovered from a version of
## auth.py duplicated at the following locations:
##      NESTS_Python/NESTS_core2/nests_core/api/entities/auth.py
##      NESTS_Python/NESTS_core2/nests_core/entities/auth.py
##      NESTS_Python/NESTS_core2/nests_core/api/entities/auth.py
##      NESTS_Python/NESTS_core/nests/api/entities/auth.py
##      NESTS_Python/NESTS_core/nests/entities/auth.py
##
## These must now be adapted for use in SLATE (and possibly future versions of
## NESTS).

# Initialize the .auth file for primary identity identified by FIP:
#def auth_initialize(fph):
#    dpath = fph_to_dpath(fph)
#    with open(dpath + "/.auth", "w") as auth_f:
#        json.dump(json_auth_tpl, auth_f)
#
# This function defined aove is obsolete.



#------------------------------------------------------------------------------
# Generate an array of three random digits, increasing and non-repeating:
def pin_random_ord():
    psi = []
    psi.append(random.randrange(0,4))
    psi.append(random.randrange(psi[0]+1,5))
    psi.append(random.randrange(psi[1]+1,6))
    return psi # list

# Generate message for PIN subset entry:
def pin_prompt_message(psi):
    message = "Please enter digits "
    message += str(psi[0] + 1) + ", "
    message += str(psi[1] + 1) + " and "
    message += str(psi[2] + 1) + " of your PIN."
    return message

def authenticate_pin(pin, pse, psi):
    pin_a = [char for char in pin]
    pse_a = [char for char in pse]
    validated = True
    for c in pse_a:
        if c != pin_a[int(c)-1]:
            validated = False
    return validated
