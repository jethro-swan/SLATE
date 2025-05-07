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

from app.core.dbm_functions import dbm_store, dbm_fetch, dbm_delete
from app.core.regexp_list import re_email
from app.core.common import nshash
from app.core.logging import log_event

#------------------------------------------------------------------------------
# Used to authenticate both passwords and recovery details (email addresses or
# phone numbers).

def auth_hash(password):
    hash_bytes = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hash_bytes.decode("utf-8")

def check_auth_hash(pwd, pwd_hash):
    try:
        pw_auth = bcrypt.checkpw(pwd.encode("utf-8"), pwd_hash.encode("utf-8"))
    except Exception as exception:
        log_event("errors", "auth_hash( )", exception)
        print(exception)
        return False
    else:
        return pw_auth






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

#==============================================================================
# Generate an access toke:

def generate_access_token():
    # An access token is generated:
    ri = random.randint(0,9999999)
    return nshash(str(random.randint(0,ri)*random.randint(0,9999999)))

# This is used mainly for command line (over SSH) access.

#==============================================================================
# PIN authetication functions:

def pin_subset_prompt(): # used in app/forms.py

    # Generate an array of three random digits, increasing and non-repeating:
    pin_subset_indices = [] # list of digit positions
    pin_subset_indices.append(random.randrange(0,3))
    pin_subset_indices.append(random.randrange(pin_subset_indices[0]+1,4))
    pin_subset_indices.append(random.randrange(pin_subset_indices[1]+1,5))

    # Then generate a prompt message for PIN subset entry:
    message = "Please enter digits "
    message += str(pin_subset_indices[0] + 1) + ", "
    message += str(pin_subset_indices[1] + 1) + " and "
    message += str(pin_subset_indices[2] + 1) + " of your PIN."

    return message, pin_subset_indices # list

def authenticate_pin( # used in app/routes.py
        pin_from_db,        # PIN retrived from database
        pin_subset_entered, # Subset of pin digits entered in login form
        pin_subset_indices  # The positions of the digits in the PIN subset
    ):

    pin_a = pin_from_db.split()
    pse_a = pin_subset_entered.split()

    validated = True
    for p in range(len(pin_subset_indices)): # the subset digit positions
        i = int(p)
        if pse_a[i] != pin_a[int(pin_subset_indices[i])]:
            validated = False
            break
    return validated

#==============================================================================
