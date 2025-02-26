#!/home/john/NESTS/SLATE/venv/bin/python3

import sys, os
import random
import string

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.fph_hrns_maps import hrns_exists_already
from app.core.slate_core import new_namespace, new_currency, new_account
from app.core.slate_core import new_primid, new_secid
from app.core.slate_core import identify_entity, get_currency_name
from app.core.slate_core import list_primid_accounts, list_secid_accounts
from app.core.slate_core import list_primid_currencies, list_secid_currencies
from app.core.slate_core import list_accounts_in_currency
from app.core.slate_core import get_entity_type
from app.core.slate_core import list_all_namespaces
from app.core.slate_core import list_all_currencies
from app.core.slate_seed import create_sandbox_root_set
from app.core.common import filename_timestamp

# A collection of new entities will be created for the purpose of running
# simulations, so it is important not to interfere with any that exist already.
#
# For the purposes of running such a simulation, single-letter names will be
# be used to a maximum depth of 4, e.g.
#   x.y.z

n_currencies = 10
n_agents = 200

l_namespaces = []
l_currencies = []
l_primids = []
l_accounts = []
l_secids = []
#print(l_namespaces)

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

print(s_fph + " > " + fph_to_hrns(s_fph))

# The steward is created:
steward_fph, \
steward_hrns, \
access_token, \
m = new_primid("jw", s_fph, "sandbox", "john@lrc.org.uk","", "pA55", "123456")
l_primids.append(steward_fph)

# An initial *currency* is created:
currency0_fph, \
currency0_hrns, \
m = new_currency("z", s_fph, steward_fph, "", "", "z")
l_currencies.append(currency0_fph)

def random_char():
    letters = string.ascii_lowercase
    return random.choice(letters)

# A collection of *namespaces* is created, starting with the sandbox root (s).
print("Creating sandbox namespaces:")

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
print("\nCreating sandbox currencies:")
c_count = 0
while c_count < n_currencies:
    n = random_char()
    currency_fph, \
    currency_hrns, \
    m = new_currency(n, random.choice(l_namespaces), steward_fph, "", "", n)
    if m:
        continue
#    print("  " + currency_hrns)
    l_currencies.append(currency_fph)
    c_count += 1

# A collection of *secids* is created, each belonging the the steward "primd*
# created above. Each has at most one *account* in any particular *currency* in
# order to simplify the simulation. This ensures that the number of *
print("\nCreating sandbox agents' identities (secids):")
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
print("\nCreating sandbox agents' accounts:")
a_count = 0
for secid_fph in l_secids:
    for currency_fph in l_currencies:
        account_fph, \
        account_hrns, \
        m = new_account(
                random_char(), random.choice(l_namespaces),
                secid_fph, currency_fph
            )
        if m:
            continue
#        print("  " + account_hrns)
        l_accounts.append(account_fph)
        a_count += 1
#if a_count != n_currencies * n_agents:
print(str(a_count) + " accounts created")

print()
print(str(c_count) + " currencies have been created:")
for currency_fph in l_currencies:
    print("\t" + fph_to_hrns(currency_fph))
print()
print(str(s_count) + " identities (agents) have been created:")
for secid_fph in l_secids:
    print("\t" + fph_to_hrns(secid_fph))
print(str(a_count) + " accounts have been created:")
for account_fph in l_accounts:
    print("\t" + fph_to_hrns(account_fph))
print()

#fname = filename_timestamp() + "_accounts_created"
fname = "accounts_created"
with open(fname, "w") as f:
    for a_count_fph in l_accounts:
        f.write(a_count_fph + "\n")
