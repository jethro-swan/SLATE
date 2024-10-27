#!/usr/bin/env python3

# TEMPORARY TEST FILE

import sys
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
from core.dbm_functions import dbm_list_entries, dbm_keys
from core.slate_core import create_entities_db
from core.payments import create_payments_db, payment, dump_currency_payments
from core.slate_core import new_namespace, new_agent, new_currency, new_account
from core.slate_core import create_seed_entities
from core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from core.slate_core import get_currency_name
from core.slate_core import list_agent_accounts, list_agent_currencies
from core.slate_core import list_currency_accounts
from core.slate_core import get_entity_type
from core.slate_core import get_auth_data
from core.slate_core import account_status
from core.common import nshash
from core.slate_core import create_quasitld_set
from core.slate_core import add_steward, remove_steward
from core.slate_core import list_stewards, list_stewardships
from core.auth import auth_hash, check_auth_hash
from core.auth import authenticate_web_access, authenticate_cli_access
from core.auth import list_password_characters, password_valid
from core.auth import generate_password, list_url_safe_password_characters
from core.auth import url_safe_password_valid, generate_url_safe_password
from core.auth import generate_access_token
from core.auth import pin_random_ord, pin_prompt_message, authenticate_pin
from core.display import integer_to_money_format
from core.display import thin_line, thick_line, title_line, thin_title_line
from core.display import yN, Yn, get_cli_number_input, pause

#==============================================================================

# Initialize Faker object
fake = Faker()
Faker.seed(24)



title_line("Creating FPH>HRNS and HRNS>FPH maps")

# The HRNS>FPH and FPH>HRNS DBM maps are created:
create_maps()

# The SQLite DBs are created:
create_entities_db()
create_payments_db()


title_line("Creating seed entities")

# The seed entities are created:
create_seed_entities()
# The seed entities' FPH>HRNS mappings will have been registered here and the
# agent is available to use:
seed_agent_hrns = "gaia.global"
seed_agent_fph, m = hrns_to_fph(seed_agent_hrns)

def check_maps():

    #print("\nList FPH>HRNS map entries\n")
    title_line("List FPH>HRNS map entries")

    fph_hrns_map = dbm_list_entries(FPH_TO_HRNS_MAP)
    for fph in fph_hrns_map.keys():
        print("\t" + fph + " > " + fph_hrns_map[fph])

    return


def list_fph_collision_map_entries():

    #print("\nList FPH collision map entries\n")
    title_line("List FPH collision map entries")

    c_map = dbm_list_entries(HRNS_C_FPH_MAP)
    for hrns in c_map.keys():
        fph = c_map[hrns]
        print("\t" + "{:>40}".format(hrns) + " > " + fph)

    return


def check_fph_hrns_mappings():

    title_line("Check HRNS>FPH mapping")

    map_keys = dbm_keys(FPH_TO_HRNS_MAP)
    for key_fph in map_keys:
        hrns = fph_to_hrns(key_fph)
        fph, m = hrns_to_fph(hrns)
        if m:
            print(m)
        if fph != key_fph:
            print("Inverse mapping incorrect")
            #title_line("Inverse mapping incorrect")
        print(key_fph + " > " + "{:>40}".format(hrns) + " > " + fph)
    print()

    return


if Yn("Check FPH>HRNS map? "):
    check_maps()

if yN("List FPH collisions? "):
    list_fph_collision_map_entries()

if Yn("Check HRNS>FPH mapping? "):
    check_fph_hrns_mappings()





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

fph, m = hrns_to_fph("gaia.global")         # seed agent "gaia.global"
if m:
    print(m)
else:
    if fph_to_hrns(fph) == "gaia.global":
        print(fph + " > " + fph_to_hrns(fph))
        l_agents = [fph]
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

#l_namespaces = [nshash("global")]           # seed namespace "global"
#l_currencies = [nshash("hours.global")]     # seed currency "hours.global"
#l_agents = [nshash("gaia.global")]          # seed agent "gaia.global"
#l_accounts = [nshash("hours.gaia.global")]  # seed account "hours.gaia.global"

def list_l_entities():
    print()
    print("Namespaces:")
    for namespace_fph in l_namespaces:
        print("\t" + namespace_fph + "\t" + fph_to_hrns(namespace_fph))
    print("Currencies:")
    for currency_fph in l_currencies:
        print("\t" + currency_fph + "\t" + fph_to_hrns(currency_fph))
    print("Agents:")
    for agent_fph in l_agents:
        print("\t" + agent_fph + "\t" + fph_to_hrns(agent_fph))
    print("Accounts:")
    for account_fph in l_accounts:
        print("\t" + account_fph + "\t" + fph_to_hrns(account_fph))
    print()

# List the seed entities:
##print("Entities in temporary lists:")
##list_l_entities()

title_line("Creating quasi-TLD root namespace set")

# Create the full set of pseudo-TLD root namespaces:
create_quasitld_set()


pause()

#
# Add a small subset of these to test namespaces list:
for hrns in ["uk", "es", "fr", "de", "ca", "us"]:
    fph, m = hrns_to_fph(hrns)
    l_namespaces.append(fph)


# Entities are selected randomly from the lists of those already available:

def select_available_namespace():
    return random.choice(l_namespaces)

def select_available_currency():
    return random.choice(l_currencies)

def select_available_agent():
    return random.choice(l_agents)

def select_available_account():
    return random.choice(l_accounts)


# For each new test agent created, its password and PIN must be recorded:
agent_credentials = {}

def record_test_agent_credentials(fph, hrns, password, pin, access_token):
    if fph: # not ""
        agent_credentials[fph] = list([hrns, password, pin, access_token])

# The first test agent is the seed agent (gaia.global) created earlier:
record_test_agent_credentials(
    seed_agent_fph,
    seed_agent_hrns,
    "Gl0balM3ltd0wn",
    "123456",
    "1a1b2c3d5e8f13g21f34e55d89e144ff"
)
# (See  slate_core.py )

def get_test_agent_hrns(fph):
    return agent_credentials[fph][1]

def get_test_agent_password(fph):
    return agent_credentials[fph][2]

def get_test_agent_pin(fph):
    return agent_credentials[fph][3]

def get_test_agent_access_token(fph):
    return agent_credentials[fph][4]



#==============================================================================
# This is a crude progress counter to indicate the sequence in which random
# entities are created or an HRNS collision detected.
progress_count = 80
def pc(char):
    global progress_count
    #print(char, end="")
    sys.stdout.write(char)
    sys.stdout.flush()
    progress_count -= 1
    if progress_count == 0:
        progress_count = 80
        sys.stdout.write("\n")
        sys.stdout.flush()


#==============================================================================
# A set of fake entities is created, each built upon a set of randomly-selected
# entities satisfying the dependency requirements:

def create_fake_entities(n):

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
        initial_steward_fph = select_available_agent()
        namespace_fph, namespace_hrns, m = new_namespace(
                                               namespace_name,
                                               parent_namespace_fph,
                                               initial_steward_fph
                                           )
        l_namespaces.append(namespace_fph)
        return namespace_fph, namespace_hrns, m

    def create_test_agent():
        parent_namespace_fph = select_available_namespace()
        parent_namespace_hrns = fph_to_hrns(parent_namespace_fph)
        agent_name = random_name()
        agent_hrns = agent_name + "." + parent_namespace_hrns
        initial_currency_fph = select_available_currency()
        initial_account_name = get_currency_name(initial_currency_fph)
        initial_account_fph, initial_account_hrns, m = new_account(
                                                           agent_hrns,
                                                           initial_currency_fph
                                                       )
        agent_realname = fake.name()
        agent_email = fake.email()
        if random.choice([0, 1]):
            initial_stewardship_fph = select_available_currency()
        else:
            initial_stewardship_fph = select_available_namespace()
        initial_stewardship_fph_list = pickle.dumps([])
        alphabet = string.ascii_letters + string.digits
        password = "".join(secrets.choice(alphabet) for i in range(16))
        p = random.randint(0,999999)
        pin = str((p*p)%1000000).zfill(6)
        agent_fph, agent_hrns, access_token, m = new_agent(
                                                     agent_name,
                                                     parent_namespace_fph,
                                                     agent_realname,
                                                     agent_email,
                                                     password,
                                                     pin,
                                                     initial_currency_fph,
                                                     initial_stewardship_fph_list
                                                 )
        #agent_credentials[agent_fph] = [agent_hrns, password, pin, access_token]
        record_test_agent_credentials(
            agent_fph, agent_hrns, password, pin, access_token
        )
        l_agents.append(agent_fph)
        return agent_fph, agent_hrns, m

    def create_test_currency():
        parent_namespace_fph = select_available_namespace()
        currency_name = random.choice([
                            "hours",
                            "kWh",
                            "g£",
                            "g$"
                        ])
        if currency_name == "hours":
            currency_prefix = ""
            currency_suffix = "h"
        elif currency_name == "kWh":
            currency_prefix = ""
            currency_suffix = "kWh"
        elif currency_name == "g£":
            currency_prefix = "g£"
            currency_suffix = ""
        elif currency_name == "g$":
            currency_prefix = "g$"
            currency_suffix = ""
        else:
            print("Something has gone very wrong here")
        initial_steward_fph = select_available_agent()
        currency_fph, currency_hrns, m = new_currency(
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

    def create_test_account(): # (beyond initial account created for each agent)
        agent_fph = select_available_agent()
        currency_fph = select_available_currency()
        account_fph, account_hrns, m = new_account(
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

    ec = 0 # count of entities created (free from HRNS collisions)
    while ec < n:
        # Create a new entity the type of which is selected randomly and the
        # dependencies of which exist only among those already created:
        e = random.choice(["namespace", "agent", "currency", "account"])
        if e == "namespace":
            fph, hrns, m = create_test_namespace()
        elif e == "agent":
            fph, hrns, m = create_test_agent()
        elif e == "currency":
            fph, hrns, m = create_test_currency()
        elif e == "account":
            fph, hrns, m = create_test_account()
#        if m:
#            print(m)
#            m_ = m.split(":")
#            if m_[0] == "collision":
#                hrns_random_duplicates.append(m)
#                hrns_random_duplicates_count += 1
#            else:
#                m__ = m_[0].split(" ")
#                if m__[0] == "Invalid":
#                    if (m__[1] == "parent") and (m__[2] == "namespace"):
#                        invalid_parent_namespace.append(m)

#        else:
#            print("{:>4}".format(ec) + "\t", end="")
#            ec += 1
#            fake_entities.append([fph, hrns, e, m])

        if fph:
            print("{:<20}".format(e), end="")
            print("{:>4}".format(ec) + "\t", end="")
            print(fph + " > " + hrns)
            ec += 1
            fake_entities.append([fph, hrns, e, m])

    print("\n")

    fe_rows = []
    for fake_entity in fake_entities:
        fe_rows.append(fake_entity)
    fe_table = PrettyTable()
    fe_table.field_names = ["FPH", "HRNS", "entity type", "error message"]
    fe_table.align = "l"
    fe_table.add_rows(fe_rows[1:])
    print(fe_table)
    print()

    print(str(100*hrns_random_duplicates_count//n) + "% HRNS collisions")
    for hrns in hrns_random_duplicates:
        print("\t" + hrns)
    print()

#    thin_line()

#    print("\nHRNS collisions found:\n")
#    for l in hrns_random_duplicates:
#        print(l)
#    print("\n")


# The set of fake entities is generated:

pause()

title_line("Generating fake entities")

print("\nPlease wait while a set of fake entities is created. ", end="")
print("This may take some time because the dependency rules must be followed.")
print()




entity_count = get_cli_number_input(
                   "How many fake entities should be created? ",
                   100, 1000, 200
               )
create_fake_entities(entity_count)

pause()

# The fake agents are listed (along with their login credentials) from the
# temporary list:
def list_fake_agents():
    fa_rows = []
    for key in agent_credentials.keys():
        agent = agent_credentials[key]
        agent.insert(0, key)
        fa_rows.append(agent)
    fa_table = PrettyTable()
    fa_table.field_names = [
                             "agent FPH",
                             "agent HRNS",
                             "password",
                             "PIN",
                             "access token"
                           ]
    fa_table.align = "l"
    fa_table.add_rows(fa_rows[1:])
    print(fa_table)


list_fake_agents()

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

        cursor.execute("SELECT * FROM agents;")
        agent_list = cursor.fetchall()
        thin_title_line("agents")
        for agent in agent_list:
            print(agent)

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
    pause()
    return

if yN("Do you want to see the fake entities' raw database entries? [yN]"):
    show_raw_database_entries_for_fake_entities()

#==============================================================================
# List each fake agent's accounts:

title_line("List the fake agents' accounts")

for agent_fph in l_agents:
    print(agent_fph + " :: " + fph_to_hrns(agent_fph))
    accounts_fph_list, m = list_agent_accounts(agent_fph)
    if m:
        print("\t" + m)
    else:
        for account_fph in accounts_fph_list:
            print("\t" + fph_to_hrns(account_fph))

thin_line()
pause()

# List currencies to which each fake agent has an account:
title_line("List the fake agents' accounts' currencies")

for agent_fph in l_agents:
    print(agent_fph + " :: " + fph_to_hrns(agent_fph))
    currencies_fph_list = list_agent_currencies(agent_fph)
    for currency_fph in currencies_fph_list:
        print("\t" + fph_to_hrns(currency_fph))

thin_line()
pause()

# List each fake currency's accounts:
title_line("List the fake currencies' accounts")

for currency_fph in l_currencies:
    print(currency_fph + " :: " + fph_to_hrns(currency_fph))
    accounts_fph_list, m = list_currency_accounts(currency_fph)
    for account_fph in accounts_fph_list:
        print("\t" + account_fph + " :: " + fph_to_hrns(account_fph))

thin_line()
pause()

#==============================================================================


def check_get_entity_type_function():

    title_line("Testing get_entity_type(entity_fph) function")

    thin_title_line("Namespaces")
    for namespace_fph in l_namespaces:
        entity_type, m = get_entity_type(namespace_fph)
        r = "{:<100}".format(namespace_fph + " > " + fph_to_hrns(namespace_fph))
        if entity_type != "namespace":
            r += " misidentified as " + entity_type + " (" + m + ")"
        else:
            r += " identified correctly as " + entity_type
        print(r)

    thin_title_line("Currencies")
    for currency_fph in l_currencies:
        entity_type, m = get_entity_type(currency_fph)
        r = "{:<100}".format(currency_fph + " > " + fph_to_hrns(currency_fph))
        if entity_type != "currency":
            r += " misidentified as " + entity_type + " (" + m + ")"
        else:
            r += " identified correctly as " + entity_type
        print(r)

    thin_title_line("Agents")
    for agent_fph in l_agents:
        entity_type, m = get_entity_type(agent_fph)
        r = "{:<100}".format(agent_fph + " > " + fph_to_hrns(agent_fph))
        if entity_type != "agent":
            r += " misidentified as " + entity_type + " (" + m + ")"
        else:
            r += " identified correctly as " + entity_type
        print(r)

    thin_title_line("Accounts")
    for account_fph in l_accounts:
        entity_type, m = get_entity_type(account_fph)
        r = "{:<100}".format(account_fph + " > " + fph_to_hrns(account_fph))
        if entity_type != "account":
            r += " misidentified as " + entity_type + " (" + m + ")"
        else:
            r += " identified correctly as " + entity_type
        print(r)

    thin_line()
    return

if yN("Do you want to test the entity type query function? [yN]"):
    check_get_entity_type_function()

#==============================================================================
# The full set of fake entities is listed againfrom the SQLite database:

def list_fake_entities_raw():

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM namespaces;")
        namespace_list = cursor.fetchall()
        thin_line()
        print("namespaces:\n")
        for namespace in namespace_list:
            print(namespace)

        cursor.execute("SELECT * FROM agents;")
        agent_list = cursor.fetchall()
        thin_line()
        print("agents:\n")
        for agent in agent_list:
            print(agent)

        cursor.execute("SELECT * FROM currencies;")
        currency_list = cursor.fetchall()
        thin_line()
        print("currencies:\n")
        for currency in currency_list:
            print(currency)

        cursor.execute("SELECT * FROM accounts;")
        account_list = cursor.fetchall()
        thin_line()
        print("accounts:\n")
        for account in account_list:
            print(account)

        cursor.close()

    thick_line()


if yN("Do you want to list the fake entities' raw database entries? [yN]"):
    list_fake_entities_raw()


#==============================================================================
# Now that we have a usefully large collection of fake accounts, we can run
# some payment tests:

pause()

def test_payment_function():
    #thick_line()
    #print("="*160)
    #print("Testing payment function:\n")
    title_line("Testing the payment( ) function")
    for currency_fph in l_currencies:
        accounts_fph_list, m = list_currency_accounts(currency_fph)
        n_accounts = len(accounts_fph_list)
        if n_accounts >= 7: # minumum number of accounts in trading set
            print(
                "\nCurrency " + fph_to_hrns(currency_fph) \
                + " has the following accounts:")
            # List the accounts in this currency:
            for account_fph in accounts_fph_list:
                print("\t" + fph_to_hrns(account_fph))
            n_payments = n_accounts * 20 # arbitrary number of test payments
            p_table = PrettyTable()
            p_table.field_names = [
                                    "payer account",
                                    "payee account",
                                    "amount",
                                    "annotation"
                                  ]
            #p_table._min_width = {
            #                        "payer account" : 40,
            #                        "payee account" : 40,
            #                        "amount" : 15
            #                     }
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

    return

#==============================================================================
def show_accounts_status(account_list):

    title_line("Show accounts' status")

    def yesno(b):
        if b:
            return "yes"
        else:
            return "no"

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

    thin_line()
    pause()
    return


show_accounts_status(l_accounts)



#test_payment_function()

def list_accounts(dtype="tuple"):
    # Now let's take another look at the accounts:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts;")
        account_list = list(cursor.fetchall())
        cursor.close()
    #print("\naccounts:\n")
    title_line("List accounts")

    if dtype == "tuple":
        #acct_rows = []
        for account in account_list:
            print(account)
    elif dtype == "table":
        acct_rows = []
        for account in account_list:
            ar = list(account)
            acct_row = []
            acct_row.append(fph_to_hrns(ar[0]))
            acct_row.append(fph_to_hrns(ar[1]))
            acct_row.append(fph_to_hrns(ar[3]))
            acct_row.append(fph_to_hrns(ar[4]))
            acct_row.append(integer_to_money_format(ar[5]))
            acct_rows.append(acct_row)
        acct_table = PrettyTable()
        acct_table.field_names = [
                                   "account HRNS",
                                   "parent namespace HRNS",
                                   "owner HRNS",
                                   "currency HRNS",
                                   "balance"
                                 ]
        acct_table.align = "r"
        #acct_table.align["account_balance"] = "r"
        acct_table.add_rows(acct_rows[1:])
        print(acct_table)

pause()
list_accounts("table")
#list_accounts()
print(
    "\nAt this point the balances will all be 0, the accounts having only" \
    + " just been created.\n"
)

test_payment_function()

list_accounts("table")
#list_accounts()
print(
    "\nSome of the account balances will no longer be 0, payments of random" \
    + " value having been made between some randomly-selected accounts in" \
    + " the same currency.\n"
)

#==============================================================================
#

def show_payments_for_test_currencies():
    title_line("Show payments made in in each currency")
    for currency_fph in l_currencies:
        print(currency_fph + " :: " + fph_to_hrns(currency_fph))
        dump_currency_payments(currency_fph)


#==============================================================================

print("\nTesting steward adding/removal\n")

test_entities = []
test_agents = []

for i in range(100):
    if random.choice([True, False]):
        entity_fph = select_available_namespace()
    else:
        entity_fph = select_available_currency()

    agent_fph = select_available_agent()
    test_entities.append(entity_fph)
    test_agents.append(agent_fph)
    add_steward(entity_fph, agent_fph)

title_line("List stewards")

for entity_fph in test_entities:
    print(fph_to_hrns(entity_fph))
    stewards, m = list_stewards(entity_fph)
    if m:
        print(m)
    for steward_fph in stewards:
        print("\t" + steward_fph + " > " + fph_to_hrns(steward_fph))

title_line("Check consistency of FPH>HRNS and HRNS>FPH mapping")
check_maps()

thin_line()
pause()

#==============================================================================


def list_stewardships():

    title_line("List stewardships")

    for agent_fph in test_agents:
        print(fph_to_hrns(agent_fph))
        stewardships, m = list_stewardships(agent_fph)
        if m:
            print(m)
        for entity_fph in stewardships:
            print("\t" + entity_fph + " > " + fph_to_hrns(entity_fph))

    return


#==============================================================================

def check_access_credentials():

    title_line("The fake and seed agents' access credentials are checked")

    agent_table = PrettyTable()
    agent_table.field_names = [
                                "agent FPH",
                                "agent HRNS",
                                "password",
                                "access_token"
                              ]
    agent_table.align = "r"
    agent_rows = []

    for agent_fph in agent_credentials.keys():

        hrns = get_test_agent_hrns(agent_fph)
        password = get_test_agent_password(agent_fph)
        pin = get_test_agent_pin(agent_fph)
        access_token = get_test_agent_access_token(agent_fph)

        auth_dict, m = get_auth_data(agent_fph)
        if m:
            print(m)
        password_hash = auth_dict["password_hash"]
        pin = auth_dict["pin"]
        access_token_hash = auth_dict["access_token_hash"]

        agent_row = []
        agent_row.append(agent_fph)
        agent_row.append(hrns)

        if check_auth_hash(password, password_hash):
            agent_row.append("authenticated")
        else:
            agent_row.append("rejected")

        if check_auth_hash(access_token, access_token_hash):
            agent_row.append("authenticated")
        else:
            agent_row.append("rejected")

        agent_rows.append(agent_row)

    agent_table.add_rows(agent_rows[1:])
    print(agent_table)

    return

#==============================================================================

pause()

if Yn("List stewardships? [Yn] "):
    list_stewardships()

if Yn("Check access credentials? [Yn] "):
    check_access_credentials()

thick_line()
