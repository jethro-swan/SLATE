#!/home/john/NESTS/SLATE/venv/bin/python3

import sys, os
import random
import string
import sys
import random
import string
import datetime, time
import shutil
import random
import argparse

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.fph_hrns_maps import hrns_exists_already
from app.core.slate_core import new_namespace, new_currency, new_account
#from app.core.slate_core import new_primid, new_secid
from app.core.slate_core import new_primid, new_ahid
from app.core.slate_core import identify_entity, get_currency_name
#from app.core.slate_core import list_primid_accounts, list_secid_accounts
from app.core.slate_core import list_primid_accounts, list_ahid_accounts
from app.core.slate_core import list_primid_currencies, list_ahid_currencies
#from app.core.slate_core import list_primid_currencies, list_secid_currencies
from app.core.slate_core import list_currency_accounts
from app.core.slate_core import get_entity_types
from app.core.slate_core import list_all_namespaces
from app.core.slate_core import list_all_currencies
from app.core.slate_seed import create_sandbox_root_set
from app.core.common import filename_timestamp
from app.core.regexp_list import *




# For each new test entity set created, the file written by the simulation
# script needs to be cleared out:
if os.path.exists("temp/payments_made"):
    os.remove("temp/payments_made")

if os.path.exists("temp/currencies_created"):
    os.remove("temp/currencies_created")


#-------------------------------------------------------------------------------
#n_currencies = 10
#n_agents = 200

# A collection of new entities will be created for the purpose of running
# simulations, so it is important not to interfere with any that exist already.
#
# For the purposes of running such a simulation, single-letter names will be
# be used to a maximum depth of 4, e.g.
#   x.y.z

l_namespaces = []
l_currencies = []
l_primids = []
l_accounts = []
l_secids = []
#print(l_namespaces)

#-------------------------------------------------------------------------------
# Defaults:
default_n_currencies    = 5
max_n_currencies        = 15
default_n_agents        = 100
max_n_agents            = 300
default_user            = "su.s"
default_email           = ""    # edit
default_password        = ""    # edit
default_pin             = ""    # edit

# Set command line options:

descriptive_blurb = "Generate a modest set of accounts for use is simple " \
                  + "simulations and demonstrations.\n\n" \
                  + "All namespaces used in the simulation are created " \
                  + "directly below the sandbox root \"s\" unless an " \
                  + "intermediate namespace is specified.\n\n" \
                  + "A number of randomly-named currencies will be created " \
                  + "in each of which there will be a significantly larger " \
                  + "number of accounts.\n\n" \
                  + "The agents in this simulation are all aliases of the " \
                  + "login user created, each limited to a single account " \
                  + "in each currency."
ap = argparse.ArgumentParser(description = descriptive_blurb)
ap.add_argument(
    "-c", "--number-of-currencies", dest = "n_currencies", action = "store",
    help = "number of currencies", default = str(default_n_currencies)
)
ap.add_argument(
    "-a", "--number-of-agents", dest = "n_agents", action = "store",
    help = "number of agents (identities)", default = str(default_n_agents)
)
#ap.add_argument(
#    "-N", "--intermediate-namespace", dest = "intermediate_namespace",
#    action = "store",
#    help = "Namespace immediately below \"s\" containing entity set."
#)
ap.add_argument(
    "-f", "--output-filename", dest = "output_filename", action = "store",
    default = "accounts_created",
    help = "Filename for list of accounts created."
)
ap.add_argument(
    "-u", "--user", dest = "user", action = "store", default = default_user,
    help = "Login identity for simulation user (default: su.s)"
)
ap.add_argument(
    "-p", "--password", dest = "pwd", action = "store",
    default = default_password,
    help = "Login password for simulation user (default: pA55)"
)
ap.add_argument(
    "-P", "--pin", dest = "pin", action = "store", default = default_pin,
    help = "Login PIN for simulation user (default: 123456)"
)
ap.add_argument(
    "-e", "--user-email", dest = "user_email", action = "store",
    default = default_email, help = "User email address"
)
args = ap.parse_args()

n_currencies = int(args.n_currencies) - 1

n_agents = int(args.n_agents)

s_fph, m = hrns_to_fph("s") # TEMPORARY

if args.output_filename is not None:
    if re_filename.match(args.output_filename):
        output_filename = args.output_filename
    else:
        output_filename = default_output_filename
else:
    output_filename = default_output_filename



if args.user is not None:
    if re_hrns.match(args.user):
        login_user = args.user.split(".")
        login_username = login_user.pop(0)
        # Does the parent namespace exist?
        login_user_parent_fph, \
        login_user_parent_hrns, \
        etype, \
        m = identify_entity(".".join(login_user))
        if (login_user_parent_fph == "") or (etype != "namespace"):
            login_user_parent_fph = s_fph
    else:
        login_username = "su"
        login_user_parent_fph = s_fph
else:
    login_username = "su"
    login_user_parent_fph = s_fph

if re_password.match(args.pwd):
    login_user_password = args.pwd
else:
    login_user_password = default_password

if re_pin.match(args.pin):
    login_user_pin = args.pin
else:
    login_user_pin = default_pin

if re_email.match(args.user_email):
    login_user_email = args.user_email
else:
    login_user_email = default_email


#==============================================================================
# A set of fake entities is created, each built upon a set of randomly-selected
# entities satisfying the dependency requirements.
#
# For the sake of simplicity
# (1) A new *primid* is created to act as the sole steward of all *namespaces*
#     and *currencies* in this set.
# (2) The number of *currencies* is limited to 10.
# (3) The total number of *identities* is limited to 200, each having no more
#     than one *account* in each of the available *currencies*.

s_fph, m = hrns_to_fph("s") # TEMPORARY
l_namespaces.append(s_fph)

#print(s_fph + " > " + fph_to_hrns(s_fph))

# The steward login *identitity* is created:
steward_fph, \
steward_hrns, \
access_token, \
m = new_primid(
        login_username,
        login_user_parent_fph,
        "sandbox",
        login_user_email,
        "",
        login_user_password,
        login_user_pin,
        "cc"
    )
l_primids.append(steward_fph)

# An initial *currency* is created:
currency0_fph, \
currency0_hrns, \
m = new_currency(
        "z",
        s_fph,
        steward_fph,
        "",
        "",
        "z",
        "",
        "",
        "",
        "",
        ""
    )
l_currencies.append(currency0_fph)

def random_char():
    letters = string.ascii_lowercase
    return random.choice(letters)

# A collection of *namespaces* is created, starting with the sandbox root (s).
print("Creating sandbox namespaces")

# Creating 100 *namesapces*:
a = ord("a")
n_count = 0
for c1 in range(10):
    n = chr(a + c1)
    namespace1_fph, \
    namespace1_hrns, \
    m = new_namespace(n, s_fph, currency0_fph, steward_fph)
#    print(str(n_count).zfill(3) + ": " + namespace1_hrns)
    l_namespaces.append(namespace1_fph)
    n_count += 1
    for c2 in range(10):
        m = chr(a + c2)
        namespace2_fph, \
        namespace2_hrns, \
        m = new_namespace(m, namespace1_fph, currency0_fph, steward_fph)
#        print(str(n_count).zfill(3) + ": " + namespace2_hrns)
        l_namespaces.append(namespace2_fph)
        n_count += 1


# A collection of *currencies* is created:
print("Creating sandbox currencies")
c_count = 0
while c_count < n_currencies:
    n = random_char()
    currency_fph, \
    currency_hrns, \
    m = new_currency(n, random.choice(l_namespaces), steward_fph, "", "", n)
    if m:
        continue
    l_currencies.append(currency_fph)
    c_count += 1

#with open("temp/edge_colours", "w") as f:
#    for currency_fph in l_currencies:
#        f.write(currency_fph)

with open("temp/currencies_created", "w") as f:
    for currency_fph in l_currencies:
        f.write(currency_fph + "\n")



# A collection of *secids* is created, each belonging the the steward "primd*
# created above. Each has at most one *account* in any particular *currency* in
# order to simplify the simulation.
s_count = 0
while s_count < n_agents:
    n = random_char()
    secid_fph, \
    secid_hrns, \
    m = new_secid(n, random.choice(l_namespaces), steward_fph)
    if m:
        continue
#    print("  " + secid_hrns)
    l_secids.append(secid_fph)
    s_count += 1

# For each of these *secids* as single *account* is created in each *currency*:
print("Creating sandbox agents' accounts")
a_count = 0
for secid_fph in l_secids:
    for currency_fph in l_currencies:
        account_fph, \
        account_hrns, \
        m = new_account(
                random_char(),
                random.choice(l_namespaces),
                secid_fph,
                currency_fph
            )
        if m:
            continue
#        print("  " + account_hrns)
        l_accounts.append(account_fph)
        a_count += 1
#if a_count != n_currencies * n_agents:
#print(str(a_count) + " accounts created")
#
#print()
#print(str(c_count) + " currencies have been created:")
#for currency_fph in l_currencies:
#    print("\t" + fph_to_hrns(currency_fph))
#print()
#print(str(s_count) + " identities (agents) have been created:")
#for secid_fph in l_secids:
#    print("\t" + fph_to_hrns(secid_fph))
#print(str(a_count) + " accounts have been created:")
#for account_fph in l_accounts:
#    print("\t" + fph_to_hrns(account_fph))
#print()

#fname = filename_timestamp() + "_accounts_created"
#name = "accounts_created"
with open("temp/" + output_filename, "w") as f:
    for a_count_fph in l_accounts:
        f.write(a_count_fph + "\n")
