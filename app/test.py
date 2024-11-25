#!/usr/bin/env python3

# TEMPORARY TEST FILE

import sys, os
from faker import Faker
import sqlite3
import random
import string
import pickle
import secrets
from prettytable import PrettyTable
from wonderwords import RandomWord

from core.constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, FPH_TO_HRNS_MAP
from core.constants import HRNS_C_FPH_MAP
from core.common import nshash
from core.common import filename_timestamp as timestamp
from core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from core.dbm_functions import dbm_list_entries, dbm_keys
from core.slate_core import create_entities_db
from core.slate_core import new_namespace, new_currency, new_account
from core.slate_core import new_primid, new_secid
from core.slate_core import identify_entity, get_currency_name
from core.slate_core import list_primid_accounts, list_secid_accounts
from core.slate_core import list_primid_currencies, list_secid_currencies
from core.slate_core import list_accounts_in_currency
from core.slate_core import get_entity_type
#from core.slate_core import get_auth_data
from core.slate_core import account_status
from core.slate_core import add_stewardship, remove_stewards
from core.slate_core import list_stewards, list_stewardships
from core.slate_core import list_active_namespaces
from core.slate_core import list_primids
from core.slate_seed import create_seed_entities, create_quasitld_set
from core.payments import create_payments_db, payment
from core.payments import dump_currency_payments_table
from core.auth import auth_hash, check_auth_hash
#from core.auth import authenticate_web_access, authenticate_cli_access
#from core.auth import authenticate_cli_access
from core.auth import list_password_characters, password_valid
from core.auth import generate_password, list_url_safe_password_characters
from core.auth import url_safe_password_valid, generate_url_safe_password
from core.auth import generate_access_token
#from core.auth import pin_random_ord, pin_prompt_message, authenticate_pin
#from core.auth import pin_random_ord, pin_prompt_message, authenticate_pin
from core.display import integer_to_money_format
from core.display import thin_line, thick_line, title_line, thin_title_line
from core.display import yN, Yn, yesno, get_cli_number_input, pause
from core.slate_login import get_auth_data
from core.logging import log_event
#from core.cctld_list import cctld_reduced_list, cctld_reduced_set
#from core.cctld_list import cctld_reduced_list2, cctld_reduced_set2

#==============================================================================
# Initialize Faker object
fake = Faker()
Faker.seed(24)

print("\nCreating FPH>HRNS and HRNS>FPH maps\n")
# The HRNS>FPH and FPH>HRNS DBM maps are created:
create_maps()


print("\nThe SQLite DBs are created\n")
# The SQLite DBs are created:
create_entities_db()
create_payments_db()


title_line("Creating seed entities")

# The seed entities are created:
create_seed_entities()

with sqlite3.connect(ENTITIES_DB) as conn:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT entity_fph, parent_namespace_fph, entity_type, active
        FROM entities_common
        """
    )
    results = cursor.fetchall()
    cursor.close()
for result in results:
    entity_fph = result[0]
    parent_namespace_fph = result[1]
    entity_type = result[2]
    active = result[3]
    print("\nentity FPH: " + entity_fph + " > " + fph_to_hrns(entity_fph))
    print("parent namespace FPH = " + parent_namespace_fph + " > " \
          + fph_to_hrns(parent_namespace_fph))
    print("entity type = " + entity_type)
    print("active? " + yesno(active))

thin_line()
#pause()


# The seed entities' FPH>HRNS mappings will have been registered here and the
# primid is available to use:
seed_primid_hrns = "gaia.global"
seed_primid_fph, m = hrns_to_fph(seed_primid_hrns)


def check_maps():

    title_line("Check consistency of FPH>HRNS and HRNS>FPH mapping")

    #print("\nList FPH>HRNS map entries\n")
    thin_title_line("List FPH>HRNS map entries")
    fph_hrns_map = dbm_list_entries(FPH_TO_HRNS_MAP)
    for fph in fph_hrns_map.keys():
        print("\t" + fph + " > " + fph_hrns_map[fph])

    #print("\nList FPH collision map entries\n")
    thin_title_line("List FPH collision map entries")

    c_map = dbm_list_entries(HRNS_C_FPH_MAP)
    for hrns in c_map.keys():
        fph = c_map[hrns]
        print("\t" + "{:>40}".format(hrns) + " > " + fph)

    thin_title_line("Check inverse mapping again")
    #title_line("Check inverse mapping again")

    map_keys = dbm_keys(FPH_TO_HRNS_MAP)
    for key_fph in map_keys:
        hrns = fph_to_hrns(key_fph)
        fph, m = hrns_to_fph(hrns)
        if m:
            print(m)
        if fph != key_fph:
            #print("Inverse mapping incorrect")
            print("Inverse mapping incorrect")
        print(key_fph + " > " + "{:>40}".format(hrns) + " > " + fph)
    print()

    thick_line()

    return


#==============================================================================
# For the purposes of these tests, a list of each randomly-generated entity is
# saved in a list, starting with the "seed" entities' FPH (which have already
# been created and registered using the  create_seed_entities()  function):

fph, m = hrns_to_fph("global")              # seed namespace "global"
if m:
    print(m)
else:
    if fph_to_hrns(fph) == "global":
        print(fph + " > " + fph_to_hrns(fph))
        l_namespaces = [fph]
    else:
        print("Should be \"global\"")

fph, m = hrns_to_fph("hours.global")        # seed currency "hours.global"
if m:
    print(m)
else:
    if fph_to_hrns(fph) == "hours.global":
        print(fph + " > " + fph_to_hrns(fph))
        l_currencies = [fph]
    else:
        print("Should be \"hours.global\"")

fph, m = hrns_to_fph("gaia.global")         # seed primid "gaia.global"
if m:
    print(m)
else:
    if fph_to_hrns(fph) == "gaia.global":
        print(fph + " > " + fph_to_hrns(fph))
        l_primids = [fph]
    else:
        print("Should be \"gaia.global\"")

fph, m = hrns_to_fph("hours.gaia.global")   # seed account "hours.gaia.global"
if m:
    print(m)
else:
    if fph_to_hrns(fph) == "hours.gaia.global":
        print(fph + " > " + fph_to_hrns(fph))
        l_accounts = [fph]
    else:
        print("Should be \"hours.gaia.global\"")

# The following arrays have been created above:
#   l_namespaces
#   l_currencies
#   l_primids
#   l_accounts
# but because no seed *secid* is required another must be created:
l_secids = []

# Entities are selected randomly from the lists of those already available:

def select_available_namespace():
    return random.choice(l_namespaces) # FPH

def select_available_currency():
    return random.choice(l_currencies) # FPH

def select_available_primid():
    return random.choice(l_primids) # FPH

def select_available_secid():
    if len(l_secids) > 2:
        return random.choice(l_secids) # FPH
    else:
        return ""

def select_available_account():
    return random.choice(l_accounts) # FPH

# The entities recorded in these temporary arrays can be displayed:
def list_l_entities():
    print()
    #thin_title_line("namespaces")
    for namespace_fph in l_namespaces:
        print("\t" + namespace_fph + "\t" + fph_to_hrns(namespace_fph))
    #thin_title_line("currencies")
    for currency_fph in l_currencies:
        print("\t" + currency_fph + "\t" + fph_to_hrns(currency_fph))
    #thin_title_line("primids")
    for primid_fph in l_primids:
        print("\t" + primid_fph + "\t" + fph_to_hrns(primid_fph))
    #thin_title_line("secids")
    for secid_fph in l_secids:
        print("\t" + secid_fph + "\t" + fph_to_hrns(secid_fph))
    #thin_title_line("accounts")
    for account_fph in l_accounts:
        print("\t" + account_fph + "\t" + fph_to_hrns(account_fph))
    print()
    thin_line()
    return

# List the seed entities:
print("\n\nEntities in temporary lists:")
list_l_entities()
pause()

if yN("Create full quasi-TLD root namespace set?"):
    title_line("Creating quasi-TLD root namespace set")
    tld_list, m = create_quasitld_set(True)
else:
    title_line("Creating reduced quasi-TLD root namespace set")
    tld_list, m = create_quasitld_set(False)
print()
for tld_fph in tld_list:
    print(tld_fph + " > " + fph_to_hrns(tld_fph))
print()

#thick_line()

# Add a small subset of these to test namespaces list:
for hrns in ["uk", "es", "fr", "de", "ca", "us"]:
    fph, m = hrns_to_fph(hrns)
    l_namespaces.append(fph)

# For each new test primid created, its password and PIN must be recorded:
primid_credentials = {}

def record_test_primid_credentials(fph, hrns, password, pin, access_token):
    if fph: # not ""
        primid_credentials[fph] = list([hrns, password, pin, access_token])

# The first test primid is the seed primid (gaia.global) created earlier:
record_test_primid_credentials(
    seed_primid_fph,
    seed_primid_hrns,
    "Gl0balM3ltd0wn",
    "123456",
    "1a1b2c3d5e8f13g21f34e55d89e144ff"
)
# (See  slate_core.py )

def get_test_primid_hrns(fph):
    return primid_credentials[fph][1]

def get_test_primid_password(fph):
    return primid_credentials[fph][2]

def get_test_primid_pin(fph):
    return primid_credentials[fph][3]

def get_test_primid_access_token(fph):
    return primid_credentials[fph][4]

#==============================================================================
# A set of fake entities is created, each built upon a set of randomly-selected
# entities satisfying the dependency requirements:

def create_fake_entities(n, a):

    print(
        "\nPlease wait while a set of " + str(n + a) + " fake entities is " \
        + "created, more than " + str(a) + " of which\nwill be accounts. " \
        + "This may take some time because the dependency rules must be\n" \
        + "followed.\n"
    )

    def random_name():
        name_length = random.randint(2,3)
        letters = string.ascii_lowercase
        n = []
        for i in range(name_length):
            n.append(random.choice(letters))
        return "".join(n)

    def random_hrns(length):
        hrnsbits = []
        for i in range(length):
            hrnsbits.append(random_name())
        return ".".join(hrnsbits)

    def fake_hrns():
        return random_hrns(random.randint(1,3))

    def create_test_namespace():
        parent_namespace_fph = select_available_namespace()
        namespace_name = random_name()
        initial_steward_fph = select_available_primid()
        namespace_fph, \
        namespace_hrns, \
        m = new_namespace(
                namespace_name,
                parent_namespace_fph,
                initial_steward_fph
            )
        l_namespaces.append(namespace_fph)
        return namespace_fph, namespace_hrns, m

    def create_test_primid():
        parent_namespace_fph = select_available_namespace()
        parent_namespace_hrns = fph_to_hrns(parent_namespace_fph)
        primid_name = random_name()
        primid_hrns = primid_name + "." + parent_namespace_hrns
        initial_currency_fph = select_available_currency()
        #initial_account_name = get_currency_name(initial_currency_fph)
        primid_realname = fake.name()
        primid_email_1 = fake.email()
        primid_email_2 = fake.email()
        if random.choice([0, 1]):
            initial_stewardship_fph = select_available_currency()
        else:
            initial_stewardship_fph = select_available_namespace()
        stewardship_fph_list = pickle.dumps([])
        alphabet = string.ascii_letters + string.digits
        password = "".join(secrets.choice(alphabet) for i in range(16))
        p = random.randint(0,999999)
        pin = str((p*p)%1000000).zfill(6)
        primid_fph, \
        primid_hrns, \
        access_token, \
        m = new_primid(
                primid_name,
                parent_namespace_fph,
                primid_realname,
                primid_email_1,
                primid_email_2,
                password,
                pin
            )
        record_test_primid_credentials(
            primid_fph, primid_hrns, password, pin, access_token
        )
        l_primids.append(primid_fph)
        return primid_fph, primid_hrns, m

    def create_test_secid():
        parent_namespace_fph = select_available_namespace()
        parent_namespace_hrns = fph_to_hrns(parent_namespace_fph)
        secid_name = random_name()
        secid_hrns = secid_name + "." + parent_namespace_hrns
        #initial_currency_fph = select_available_currency()
        owner_primid_fph = select_available_primid()
        secid_fph, secid_hrns, m = new_secid(
                                       secid_name,
                                       parent_namespace_fph,
                                       owner_primid_fph
                                   )
        l_secids.append(secid_fph)
        return secid_fph, secid_hrns, m

    def create_test_currency():
        parent_namespace_fph = select_available_namespace()
        currency_name = random_name()
        #parent_namespace_hrns = fph_to_hrns(parent_namespace_fph)
        currency_type = random.choice(["hours", "kWh", "g£", "g$"])
        if currency_type == "hours":
            currency_prefix = ""
            currency_suffix = "h"
        elif currency_type == "kWh":
            currency_prefix = ""
            currency_suffix = "kWh"
        elif currency_type == "g£":
            currency_prefix = "g£"
            currency_suffix = ""
        elif currency_type == "g$":
            currency_prefix = "g$"
            currency_suffix = ""
        else:
            currency_prefix = ""
            currency_suffix = ""

        initial_steward_fph = select_available_primid()
        currency_fph, \
        currency_hrns, \
        m = new_currency(
                currency_name,
                parent_namespace_fph,
                initial_steward_fph,
                currency_prefix,
                currency_suffix
            )
        if m:
            return "", "", m
        l_currencies.append(currency_fph)
        return currency_fph, currency_hrns, m

    def create_test_account():
        account_namesapace_hrns = fph_to_hrns(select_available_namespace())
        account_hrns = random_name() + "." + account_namesapace_hrns
        # In early iterations, the l_secids list may be empty so that must be
        # checked:
##        agent_fph = select_available_secid()
        if random.choice([True, False]): # if not ""
            agent_fph = select_available_primid()
        else:
            agent_fph = select_available_secid()
            if not agent_fph:
                agent_fph = select_available_primid()
        currency_fph = select_available_currency()
        account_fph, \
        account_hrns, \
        m = new_account(
                account_hrns,
                agent_fph,
                currency_fph
            )
        if m:
            return "", "", m
        l_accounts.append(account_fph)
        return account_fph, account_hrns, m

    fake_entities = []

    # The following list and count are used to get an idea of the likely number
    # of random collisions:
    hrns_random_duplicates = []
    hrns_random_duplicates_count = 0

    invalid_parent_namespace = []

    namespace_count = 0
    primid_count = 0
    secid_count = 0
    currency_count = 0
    account_count = 0

    error_messages = []
    error_count = 0

    print("-"*80)
    print("{:>6}".format("entity") + "\t", end="")
    print("{:<10}".format("entity"), end="")
    print("{:>8}".format("error"))
    print("{:>6}".format("count") + "\t", end="")
    print("{:<10}".format("type"), end="")
    print("{:>8}".format("count"), end="")
    print("    ", end="")
    print("entity FPH" + " "*22 + " > entity HRNS")
    print("-"*80)

    ec = 0 # count of initial entities to be created (free from HRNS collisions)
    while ec < n:
        # Create a new entity the type of which is selected randomly and the
        # dependencies of which exist only among those already created:
        e = random.choice([
                            "namespace",
                            "primid",
                            "secid",
                            "currency",
                            "account"
                         ])
        if e == "namespace":
            fph, hrns, m = create_test_namespace()
            if m:
                error_messages.append(m)
                error_count += 1
            else:
                namespace_count += 1
        elif e == "primid":
            fph, hrns, m = create_test_primid()
            if m:
                error_messages.append(m)
                error_count += 1
            else:
                primid_count += 1
        elif e == "secid":
            fph, hrns, m = create_test_secid()
            if m:
                error_messages.append(m)
                error_count += 1
            else:
                secid_count += 1
        elif e == "currency":
            fph, hrns, m = create_test_currency()
            if m:
                error_messages.append(m)
                error_count += 1
            else:
                currency_count += 1
        elif e == "account":
            fph, hrns, m = create_test_account()
            if m:
                error_messages.append(m)
                error_count += 1
            else:
                account_count += 1

        #if m:
        #    print(m)

        if fph:
            print("{:>6}".format(ec) + "\t", end="")
            print("{:<10}".format(e), end="")
            print("{:>8}".format(error_count), end="")
            print("    ", end="")
            print(fph + " > " + hrns)
            #print(fph + " > " + hrns, end="")
            #print("    " + m)
            ec += 1
            fake_entities.append([fph, hrns, e, m])

    # In general there will be far more accounts than other entities, so now
    # an extra set of accounts will be created.

    ac = 0 # loop counter for additional accounts
    while ac < a:
        fph, hrns, m = create_test_account()
        if m:
            error_messages.append(m)
            error_count += 1
        else:
            account_count += 1
        if fph:
            print("{:>6}".format(ec) + "\t", end="")
            print("{:<10}".format("account"), end="")
            print("{:>8}".format(error_count), end="")
            print("    ", end="")
            print(fph + " > " + hrns)
            ac += 1 # count of additional accounts
            ec += 1 # total count of entities
            fake_entities.append([fph, hrns, "account", m])

    #print("\n")
    print("\nError count = " + str(error_count) + "\n")

    fe_rows = []
    for fake_entity in fake_entities:
        fe_rows.append(fake_entity)
    fe_table = PrettyTable()
    fe_table.field_names = ["FPH", "HRNS", "entity type", "error message"]
    fe_table.align = "l"
    fe_table.add_rows(fe_rows[1:])
    print(fe_table)
    print()

    fname = os.getcwd() + "/fake_entities_list.txt"
    with open(fname, "w") as f:
        f.write("\n" + str(fe_table) + "\n\n")
    print("\nA copy of the table above has been written to " + fname + "\n")

    pause()

    print(str(100*hrns_random_duplicates_count//n) + "% HRNS collisions")
    for hrns in hrns_random_duplicates:
        print("\t" + hrns)
    print()

    e_count = namespace_count + currency_count + primid_count + secid_count \
            + account_count
    if e_count == n:
        print("{:2.2f}".format(100*namespace_count/n) + "% namespaces")
        print("{:2.2f}".format(100*currency_count/n) + "% currencies")
        print("{:2.2f}".format(100*primid_count/n) + "% primids")
        print("{:2.2f}".format(100*secid_count/n) + "% secids")
        print("{:2.2f}".format(100*account_count/n) + "% accounts")
    print()

    if Yn("Show error messages?"):
        for error_message in error_messages:
            print(error_message)
    else:
        print()

    pause()
    thick_line()
    return

# The set of fake entities is generated:

#pause()

title_line("Generating fake entities")
#
entity_count = get_cli_number_input(
                   "How many fake entities should be created initially? ",
                   100, 500, 200
               )
# IMPORTANT:
# Each agent (whether *primid* or *secid*) can have only one *account* in each
# *currency*, therefore the restricting the *account* names to the *agent*s'
# personal *namespaces* would create a problem.


additional_accounts = round(entity_count * 0.5)
# NB: If this number is too low the threshold to run the payments tests will
#     not usually be reached.
#     If this number is too high, the tests may take far too long to run.
#     By experimentation, it has been found that 0 is a bit too low and 2 is
#     far too high.
#
print(
    "The number of accounts will be far greater than that of the other" \
    + " entitity types\nso a further " + str(additional_accounts) \
    + " accounts will be added."
)
create_fake_entities(entity_count, additional_accounts)

#==============================================================================
# The fake agents are listed (along with their login credentials) from the
# temporary list:
def list_fake_primids_from_temporary_list():
    fa_rows = []
    for key in primid_credentials.keys():
        primid = primid_credentials[key]
        primid.insert(0, key)
        fa_rows.append(primid)
    fa_table = PrettyTable()
    fa_table.field_names = [
                             "primid FPH",
                             "primid HRNS",
                             "password",
                             "PIN",
                             "access token"
                           ]
    fa_table.align = "l"
    fa_table.add_rows(fa_rows[1:])
    print(fa_table)

    fname = os.getcwd() \
          + "/fake_primids_access_credentials_" + timestamp() + ".txt"
    with open(fname, "w") as f:
        f.write("\n" + str(fa_table) + "\n\n")
    print("\nA copy of the table above has been written to " + fname + "\n")

list_fake_primids_from_temporary_list()

thick_line()
pause()

#==============================================================================
# The full set of fake entities is now listed, this time extracted from the
# (temporary) SQLite database:

def show_raw_database_entries_for_fake_entities():

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM namespaces;")
        namespace_list = cursor.fetchall()
        thin_title_line("namespaces")
        for namespace in namespace_list:
            print(namespace)
        pause()

        cursor.execute("SELECT * FROM primids;")
        primid_list = cursor.fetchall()
        thin_title_line("primids")
        for primid in primid_list:
            print(primid)
        pause()

        cursor.execute("SELECT * FROM secids;")
        secid_list = cursor.fetchall()
        thin_title_line("secids")
        for secid in secid_list:
            print(secid)
        pause()

        cursor.execute("SELECT * FROM currencies;")
        currency_list = cursor.fetchall()
        thin_title_line("currencies")
        for currency in currency_list:
            print(currency)
        pause()

        cursor.execute("SELECT * FROM accounts;")
        account_list = cursor.fetchall()
        thin_title_line("accounts")
        for account in account_list:
            print(account)

        cursor.close()

    thick_line()
    pause()
    return

if Yn("Do you want to see the fake entities' raw database entries?"):
    show_raw_database_entries_for_fake_entities()
else:
    print()

#==============================================================================
# The following entities and relationships are listed from the temporary lists
# in this script:
# - the accounts belonging to each of the fake primids
# - the currencies in which each fake primid has as account
# - the accounts associated with each currency

def list_fake_entities_relationships_from_test_lists():

    # List each fake primid's accounts:

    title_line("List the fake primids' accounts (from l_primids[ ] list)")

    for primid_fph in l_primids:
        print(primid_fph + " > " + fph_to_hrns(primid_fph))
        accounts_fph_list, m = list_primid_accounts(primid_fph)
        if m:
            print("\t" + m)
        else:
            for account_fph in accounts_fph_list:
                print("\t" + fph_to_hrns(account_fph))

    thin_line()
    pause()

    # List currencies in which each fake primid has an account:
    title_line("List the fake primids' accounts' currencies")

    for primid_fph in l_primids:
        print(primid_fph + " > " + fph_to_hrns(primid_fph))
        currencies_fph_list = list_primid_currencies(primid_fph)
        for currency_fph in currencies_fph_list:
            print("\t" + fph_to_hrns(currency_fph))

    thin_line()
    pause()

    title_line("List the fake secids' accounts (from l_secids[ ] list)")

    for secid_fph in l_secids:
        print(secid_fph + " > " + fph_to_hrns(secid_fph))
        accounts_fph_list, m = list_secid_accounts(secid_fph)
        if m:
            print("\t" + m)
        else:
            for account_fph in accounts_fph_list:
                print("\t" + fph_to_hrns(account_fph))

    thin_line()
    pause()

    # List currencies in which each fake secid has an account:
    title_line("List the fake secids' accounts' currencies")

    for secid_fph in l_secids:
        print(secid_fph + " > " + fph_to_hrns(secid_fph))
        currencies_fph_list = list_secid_currencies(secid_fph)
        for currency_fph in currencies_fph_list:
            print("\t" + fph_to_hrns(currency_fph))

    thin_line()
    pause()

    # List each fake currency's accounts:
    title_line("List the fake currencies' accounts")

    for currency_fph in l_currencies:
        print(currency_fph + " > " + fph_to_hrns(currency_fph))
        accounts_fph_list, m = list_accounts_in_currency(currency_fph)
        if m:
            print(m)
        for account_fph in accounts_fph_list:
            print("\t" + account_fph + " > " + fph_to_hrns(account_fph))

    #thin_line()
    #pause()

    thick_line()

if Yn("List the fake entities' relationships from test lists?"):
    list_fake_entities_relationships_from_test_lists()

#==============================================================================
# Check that each entity's type can be identified correctly from the database.

def check_get_entity_type_function():

    title_line("Testing get_entity_type(entity_fph) function")

    thin_title_line("namespaces")
    for namespace_fph in l_namespaces:
        entity_type, m = get_entity_type(namespace_fph)
        r = "{:<80}".format(namespace_fph + " > " + fph_to_hrns(namespace_fph))
        if entity_type != "namespace":
            r += " misidentified as " + entity_type + " (" + m + ")"
        else:
            r += " correct (" + entity_type + ")"
        print(r)

    thin_title_line("currencies")
    for currency_fph in l_currencies:
        entity_type, m = get_entity_type(currency_fph)
        r = "{:<80}".format(currency_fph + " > " + fph_to_hrns(currency_fph))
        if entity_type != "currency":
            r += " misidentified as " + entity_type + " (" + m + ")"
        else:
            r += " correct (" + entity_type + ")"
        print(r)

    thin_title_line("primids")
    for primid_fph in l_primids:
        entity_type, m = get_entity_type(primid_fph)
        r = "{:<80}".format(primid_fph + " > " + fph_to_hrns(primid_fph))
        if entity_type != "primid":
            r += " misidentified as " + entity_type + " (" + m + ")"
        else:
            r += " correct (" + entity_type + ")"
        print(r)

    thin_title_line("secids")
    for secid_fph in l_secids:
        etype, m = get_entity_type(secid_fph)
        r = "{:<80}".format(secid_fph + " > " + fph_to_hrns(secid_fph))
        if etype != "secid":
            r += " misidentified as " + etype + " (" + m + ")"
        else:
            r += " correct (" + etype + ")"
        print(r)

    thin_title_line("accounts")
    for account_fph in l_accounts:
        entity_type, m = get_entity_type(account_fph)
        r = "{:<80}".format(account_fph + " > " + fph_to_hrns(account_fph))
        if entity_type != "account":
            r += " misidentified as " + entity_type + " (" + m + ")"
        else:
            r += " correct (" + entity_type + ")"
        print(r)

    thin_line()
    return

if Yn("Do you want to test the entity type query function?"):
    check_get_entity_type_function()
else:
    print()

#==============================================================================
# The full set of fake entities is listed againfrom the SQLite database:

def list_fake_entities_raw():

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM namespaces;")
        namespace_list = cursor.fetchall()
        thin_title_line("namespaces")
        for namespace in namespace_list:
            print(namespace)

        cursor.execute("SELECT * FROM primids;")
        primid_list = cursor.fetchall()
        thin_title_line("primids")
        for primid in primid_list:
            print(primid)

        cursor.execute("SELECT * FROM secids;")
        secid_list = cursor.fetchall()
        thin_title_line("secids")
        for secid in secid_list:
            print(secid)

        cursor.execute("SELECT * FROM currencies;")
        currency_list = cursor.fetchall()
        thin_title_line("currencies")
        for currency in currency_list:
            print(currency)

        cursor.execute("SELECT * FROM accounts;")
        account_list = cursor.fetchall()
        thin_title_line("accounts")
        for account in account_list:
            print(account)

        cursor.close()

    thick_line()


if Yn("Do you want to list the fake entities' raw database entries?"):
    list_fake_entities_raw()
else:
    print()


#==============================================================================
# Now that we have a usefully large collection of fake accounts, we can run
# some payment tests:

#pause()

def test_payment_function():
    #thick_line()
    #print("="*160)
    #print("Testing payment function:\n")
    title_line("Testing the payment( ) function")
    for currency_fph in l_currencies:
        accounts_fph_list, m = list_accounts_in_currency(currency_fph)

        n_accounts = len(accounts_fph_list)
        if n_accounts >= 7: # minumum number of accounts in trading set
        #if n_accounts < 7: # minumum number of accounts in trading set
            print(
                "\nCurrency " + fph_to_hrns(currency_fph) \
                + " has the following " + str(n_accounts) + " accounts:"
            )
            # List the accounts in this currency:
            for account_fph in accounts_fph_list:
                print("\t" + fph_to_hrns(account_fph))

            n_payments = n_accounts * random.randint(15,30) # arbitrary number
                                                            # of test payments
            print(
                "Please be patient while a set of " + str(n_payments) \
                + " payments is made between pairs selected at random " \
                + "from the set of accounts in currency \"" \
                + fph_to_hrns(currency_fph) + "\" (" + currency_fph + ")."
            )
            p_table = PrettyTable()
            p_table.field_names = [
                                    "payer account",
                                    "payee account",
                                    "amount",
                                    "annotation"
                                  ]
            p_rows = []
            for p in range(n_payments):
                p_row = []
                payer_fph = random.choice(accounts_fph_list)
                payee_fph = random.choice(accounts_fph_list)
                if payer_fph != payee_fph:
                    amount = random.randint(1, 100000)
                    rword = RandomWord()
                    rwords = rword.random_words(3) # list
                    annotation = " ".join(rwords)
                    # Record the payment in the databases:
                    m = payment(payer_fph, payee_fph, amount, annotation)
                    if m:
                        print(m)
                    # Add payment to test table:
                    p_row.append(fph_to_hrns(payer_fph))
                    p_row.append(fph_to_hrns(payee_fph))
                    p_row.append(integer_to_money_format(amount))
                    p_row.append(annotation)
                    p_rows.append(p_row)
            p_table.align = "r"
            p_table.align["annotation"] = "l"
            p_table.add_rows(p_rows[1:])
            print(p_table)

    #    else:
    #        print("ping!!!!")

    thin_line()
    pause()
    return

#==============================================================================
def show_accounts_status(account_list):

    title_line("Show accounts' status")

    acct_rows = []
    acct_table = PrettyTable()
    acct_table.field_names = [
                               "account HRNS",
                               "exists",
                               "active",
                               "currency",
                               "owner",
                               "balance",
                               "error message"
                             ]
    acct_table.align = "l"

    for account_fph in account_list:
        #print("account_fph = " + account_fph)
        account_exists, \
        account_active, \
        account_currency_fph, \
        account_owner_fph, \
        account_balance, \
        m = account_status(account_fph)
        acct_row = []
        acct_row.append(fph_to_hrns(account_fph))
        acct_row.append(yesno(account_exists))
        acct_row.append(yesno(account_active))
        acct_row.append(fph_to_hrns(account_currency_fph))
        acct_row.append(fph_to_hrns(account_owner_fph))
        acct_row.append(integer_to_money_format(account_balance))
        acct_row.append(m)
        acct_rows.append(acct_row)

    acct_table.add_rows(acct_rows[1:])
    print(acct_table)

    thick_line()
    pause()
    return


if Yn("Show the status of the accounts in the l_accounts list?"):
    show_accounts_status(l_accounts)
else:
    print("\n")



#test_payment_function()

def list_accounts(save):
    thin_title_line("These are the accounts:")
    # Now let's take another look at the accounts:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        #cursor.execute("SELECT entity_fph FROM accounts")
        cursor.execute("SELECT * FROM accounts")
        #account_list = list(cursor.fetchall())
        account_list = cursor.fetchall()
        #print("account_list has type = " + str(type(account_list)))
        cursor.close()

    if Yn("(Show raw database row for accounts?)"):
        for account_row in account_list:
            print(account_row)
        thin_line()
    else:
        print()

    title_line("List accounts")
    acct_rows = []

    #for account_fph in account_list:
    for account_row in account_list:
        account_fph = account_row[0]
        #account_fph = list(account_row[0])
        account_exists, \
        account_active, \
        account_currency_fph, \
        account_owner_fph, \
        account_balance, \
        m = account_status(account_fph)
        #ar = list(account)
        acct_row = []
        acct_row.append(fph_to_hrns(account_fph))   # account HRNS
        acct_row.append(yesno(account_exists))
        acct_row.append(yesno(account_active))
        acct_row.append(fph_to_hrns(account_currency_fph))
        acct_row.append(fph_to_hrns(account_owner_fph))
        acct_row.append(integer_to_money_format(account_balance))
        acct_row.append(m)
        acct_rows.append(acct_row)

    acct_table = PrettyTable()
    acct_table.field_names = [
                               "account HRNS",
                               "exists",
                               "active",
                               "currency HRNS",
                               "owner HRNS",
                               "balance",
                               "error message"
                              ]
    acct_table.align = "l"
    acct_table.align["balance"] = "r"
    acct_table.add_rows(acct_rows[1:])
    print(acct_table)

    if save:
        fname = os.getcwd() + "/fake_accounts_list_" + timestamp() + ".txt"
        with open(fname, "w") as f:
            f.write("\n" + str(acct_table) + "\n\n")
        print("\nA copy of this table has been written to " + fname + "\n")

    thick_line()
    return

#pause()
if Yn("List accounts?"):
    list_accounts(False) # before payments
#list_accounts()
print(
    "\nAt this point the balances will all be 0, the accounts having only" \
    + " just been created.\n"
)

test_payment_function()

if Yn("List accounts?"):
    list_accounts(True) # after payments
else:
    print("\n")
#list_accounts()
print(
    "\nSome of the account balances will no longer be 0, payments of random" \
    + " value having been made between some randomly-selected accounts in" \
    + " the same currency.\n"
)

#==============================================================================
#

def show_payments_for_test_currencies():
    title_line("Show payments made in each currency")
    for currency_fph in l_currencies:



        print(currency_fph + " > " + fph_to_hrns(currency_fph))
        print(dump_currency_payments_table(currency_fph, ""))


if Yn("List the payments that have been made in each currency?"):
    show_payments_for_test_currencies()
else:
    print("\n")

#==============================================================================
#

def test_steward_add_remove():

    title_line("Testing steward adding/removal")

    test_entities = []
    test_stewards = []

    for i in range(100):
        if random.choice([True, False]):
            stewarded_entity_fph = select_available_namespace()
        else:
            stewarded_entity_fph = select_available_currency()

        steward_fph = select_available_primid()
        test_entities.append(stewarded_entity_fph)
        test_stewards.append(steward_fph)
        m = add_stewardship(stewarded_entity_fph, steward_fph)
        if m:
            print(m)

    title_line("List stewards")

    for stewarded_entity_fph in test_entities:
        print(fph_to_hrns(stewarded_entity_fph))
        stewards, m = list_stewards(stewarded_entity_fph)
        if m:
            print(m)
        for steward_fph in stewards:
            print("\t" + steward_fph + " > " + fph_to_hrns(steward_fph))

    return

if Yn("Test steward adding/removal?"):
    test_steward_add_remove()
    thick_line()
    pause()
else:
    print("\n")

#==============================================================================

if yN("Check consistency of FPH>HRNS and HRNS>FPH mapping?"):
    check_maps()
    thick_line()
    pause()
else:
    print()

#==============================================================================

def list_active_primids_from_database():

    title_line("Listing active primids from database")

    primid_fph_list, m = list_primids("active")
    if m:
        print(m)
    for primid_fph in primid_fph_list:
        print(fph_to_hrns(primid_fph))

    thick_line()


if Yn("List active primids from database?"):
    list_active_primids_from_database()
    thick_line()
    pause()
else:
    print("\n")




#==============================================================================


def list_stewardships_from_database():

    title_line("Listing stewardships held by each primid")

    primid_fph_list, m = list_primids("active")
    if m:
        print(m)
    for primid_fph in primid_fph_list:
        print(fph_to_hrns(primid_fph))
        stewardships, m = list_stewardships(primid_fph)
        if m:
            print(m)
        for entity_fph in stewardships:
            print("\t" + entity_fph + " > " + fph_to_hrns(entity_fph))

    thick_line()
    pause()
    return

if Yn("List stewardships?"):
    list_stewardships_from_database()
else:
    print("\n")

#==============================================================================
# The access credentials of the primids recorded in the database are checked
# against those in the primid_credentials dictionary created earlier.

def check_access_credentials():

    title_line(
        "The fake and seed primids' access credentials will now be checked"
    )

    primid_table = PrettyTable()
    primid_table.field_names = [
                                 "primid FPH",
                                 "primid HRNS",
                                 "password",
                                 "access_token"
                               ]
    primid_table.align = "r"
    primid_rows = []

    print("Authenticating access for: ")

    for primid_fph in primid_credentials.keys():

        hrns = get_test_primid_hrns(primid_fph)
        password = get_test_primid_password(primid_fph)
        pin = get_test_primid_pin(primid_fph)
        access_token = get_test_primid_access_token(primid_fph)

        print("\t" + hrns)

#        auth_dict, m = get_auth_data(primid_fph)
#        if m:
#            print(m)
#        password_hash = auth_dict["password_hash"]
#        pin = auth_dict["pin"]
#        access_token_hash = auth_dict["access_token_hash"]

        password_hash, \
        pin, \
        access_token_hash, \
        m = get_auth_data(primid_fph)
        if m:
            print(m)

        print("password hash = " + password_hash)
        print("PIN = " + pin)
        print("access_token_hash = " + access_token_hash)

        primid_row = []
        primid_row.append(primid_fph)
        primid_row.append(hrns)

        if check_auth_hash(password, password_hash):
            primid_row.append("authenticated")
        else:
            primid_row.append("rejected")

        if check_auth_hash(access_token, access_token_hash):
            primid_row.append("authenticated")
        else:
            primid_row.append("rejected")

        primid_rows.append(primid_row)

    primid_table.add_rows(primid_rows[1:])
    print(primid_table)

    thick_line()
    pause()
    return

if Yn("Check the fake primids' access credentials?"):
    check_access_credentials()
else:
    print("\n")

#==============================================================================


if Yn("List the active namespaces from database?"):

    title_line("Listing the active namespaces from the database")

    namespace_fph_list, m = list_active_namespaces()
    if m:
        print(m)
    for fph in namespace_fph_list:
        print(fph + " > " + fph_to_hrns(fph))
    print("\n")
    thick_line()

else:
    print("\n")

#==============================================================================
if yN("Check  identify_entity( )  consistency?"):

    errors = []

    for namespace_fph in l_namespaces:
        a_entity_fph, \
        a_entity_hrns, \
        a_etype, \
        m = identify_entity(namespace_fph)
        if m:
            errors.append(m)
        print(a_etype + " \t " + a_entity_fph + " > " + a_entity_hrns)
        b_entity_fph, \
        b_entity_hrns, \
        b_etype, \
        m = identify_entity(a_entity_hrns)
        if m:
            errors.append(m)
        print(b_etype + " \t " + b_entity_fph + " < " + b_entity_hrns)
        if a_entity_fph != b_entity_fph:
            print("FPH mismatch: " + a_entity_fph + " and " + b_entity_fph)
        if a_entity_hrns != b_entity_hrns:
            print("FPH mismatch: " + a_entity_hrns + " and " + b_entity_hrns)
        if a_etype != b_etype:
            print("Entity type mismatch: " + a_etype + " and " + b_etype)

    for currency_fph in l_currencies:
        a_entity_fph, \
        a_entity_hrns, \
        a_etype, \
        m = identify_entity(currency_fph)
        if m:
            errors.append(m)
        print(a_etype + " \t " + a_entity_fph + " > " + a_entity_hrns)
        b_entity_fph, \
        b_entity_hrns, \
        b_etype, \
        m = identify_entity(a_entity_hrns)
        if m:
            errors.append(m)
        print(b_etype + " \t " + b_entity_fph + " < " + b_entity_hrns)
        if a_entity_fph != b_entity_fph:
            print("FPH mismatch: " + a_entity_fph + " and " + b_entity_fph)
        if a_entity_hrns != b_entity_hrns:
            print("FPH mismatch: " + a_entity_hrns + " and " + b_entity_hrns)
        if a_etype != b_etype:
            print("Entity type mismatch: " + a_etype + " and " + b_etype)

    for account_fph in l_accounts:
        a_entity_fph, \
        a_entity_hrns, \
        a_etype, \
        m = identify_entity(account_fph)
        if m:
            errors.append(m)
        print(a_etype + " \t " + a_entity_fph + " > " + a_entity_hrns)
        b_entity_fph, \
        b_entity_hrns, \
        b_etype, \
        m = identify_entity(a_entity_hrns)
        if m:
            errors.append(m)
        print(b_etype + " \t " + b_entity_fph + " < " + b_entity_hrns)
        if a_entity_fph != b_entity_fph:
            print("FPH mismatch: " + a_entity_fph + " and " + b_entity_fph)
        if a_entity_hrns != b_entity_hrns:
            print("FPH mismatch: " + a_entity_hrns + " and " + b_entity_hrns)
        if a_etype != b_etype:
            print("Entity type mismatch: " + a_etype + " and " + b_etype)

    for primid_fph in l_primids:
        a_entity_fph, \
        a_entity_hrns, \
        a_etype, \
        m = identify_entity(primid_fph)
        if m:
            errors.append(m)
        print(a_etype + " \t\t " + a_entity_fph + " > " + a_entity_hrns)
        b_entity_fph, \
        b_entity_hrns, \
        b_etype, \
        m = identify_entity(a_entity_hrns)
        if m:
            errors.append(m)
        print(b_etype + " \t\t " + b_entity_fph + " < " + b_entity_hrns)
        if a_entity_fph != b_entity_fph:
            print("FPH mismatch: " + a_entity_fph + " and " + b_entity_fph)
        if a_entity_hrns != b_entity_hrns:
            print("FPH mismatch: " + a_entity_hrns + " and " + b_entity_hrns)
        if a_etype != b_etype:
            print("Entity type mismatch: " + a_etype + " and " + b_etype)

    for secid_fph in l_secids:
        a_entity_fph, \
        a_entity_hrns, \
        a_etype, \
        m = identify_entity(secid_fph)
        if m:
            errors.append(m)
        print(a_etype + " \t\t " + a_entity_fph + " > " + a_entity_hrns)
        b_entity_fph, \
        b_entity_hrns, \
        b_etype, \
        m = identify_entity(a_entity_hrns)
        if m:
            errors.append(m)
        print(b_etype + " \t\t " + b_entity_fph + " < " + b_entity_hrns)
        if a_entity_fph != b_entity_fph:
            print("FPH mismatch: " + a_entity_fph + " and " + b_entity_fph)
        if a_entity_hrns != b_entity_hrns:
            print("FPH mismatch: " + a_entity_hrns + " and " + b_entity_hrns)
        if a_etype != b_etype:
            print("Entity type mismatch: " + a_etype + " and " + b_etype)

    print("\nErrors:\n")
    for i in range(len(errors)):
        print(errors[i])
    print()

    thick_line()
