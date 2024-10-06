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
from core.dbm_functions import dbm_list_entries
from core.slate_core import create_entities_db
from core.payments import create_payments_db, payment, dump_currency_payments
from core.slate_core import new_namespace, new_agent, new_currency, new_account
from core.slate_core import create_seed_entities
from core.fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from core.slate_core import get_currency_name
from core.slate_core import list_agent_accounts, list_agent_currencies
from core.slate_core import list_currency_accounts
from core.slate_core import get_entity_type
from core.common import nshash
from core.auth import auth_hash
from core.display import integer_to_money_format
from core.slate_core import create_pseudotld_set
from core.slate_core import add_steward, remove_steward
from core.slate_core import list_stewards, list_stewardships

# TEMPORARY TEST BITS


# Initialize Faker object
fake = Faker()
Faker.seed(24)

#
print("\nPlease wait while a set of fake entities is created. ", end="")
print("This may take some time because the dependency rules must be followed.")
print()

# The HRNS>FPH and FPH>HRNS DBM maps are created:
create_maps()

# The SQLite DBs are created:
create_entities_db()
create_payments_db()


# The seed entities are created:
create_seed_entities()


def random_name():
    name_length = random.randint(2,3)
    letters = string.ascii_lowercase
    n = []
    for i in range(name_length):
        n.append(random.choice(letters))
    return "".join(n)
    #name = "".join(n)                       # Temporaryt debuggery
    #print("\t\t" + name)                    #
    #return name                             #

def random_hrns(length):
    hrnsbits = []
    for i in range(length):
        hrnsbits.append(random_name())
    return ".".join(hrnsbits)
    #hrns = ".".join(hrnsbits)               # Temporaryt debuggery
    #print("\t" + hrns)                      #
    #return hrns                             #

def fake_hrns():
    return random_hrns(random.randint(1,3))
    #hrns = random_hrns(random.randint(1,3)) # Temporaryt debuggery
    #print("\t\t\t" + hrns)                  #
    #return hrns                             #

def test_hrns_faker():
    print()
    print("A random name:\t" + random_name())
    print("A random HRNS:\t" + random_hrns(3))
    print("A random fake:\t" + fake_hrns())
    print()

#test_hrns_faker()



# For the purposes of these tests, a list of each randomly-generated entity is
# saved in a list, starting with the "seed" entities' FPH:
l_namespaces = [nshash("global")]           # seed namespace "global"
l_currencies = [nshash("hours.global")]     # seed currency "hours.global"
l_agents = [nshash("gaia.global")]          # seed agent "gaia.global"
l_accounts = [nshash("hours.gaia.global")]  # seed account "hours.gaia.global"

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

# Create the full set of pseudo-TLD root namespaces:
create_pseudotld_set()
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
    agent_credentials[fph] = [hrns, password, pin, access_token]

def get_test_agent_hrns(fph):
    return agent_credentials[fph][0]

def get_test_agent_password(fph):
    return agent_credentials[fph][1]

def get_test_agent_pin(fph):
    return agent_credentials[fph][2]

def get_test_agent_access_token(fph):
    return agent_credentials[fph][3]


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

    agent_credentials[agent_fph] = [agent_hrns, password, pin, access_token]

    l_agents.append(agent_fph)

    return agent_fph, agent_hrns, m


def create_test_currency():

    parent_namespace_fph = select_available_namespace()
    #currency_name = random_name()
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


def create_test_account(): # (beyond the initial account created for each agent)

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


#==============================================================================
# A set of fake entities is created, each built upon a set of randomly-selected
# entities satisfying the dependency requirements:

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

def create_fake_entities(n):

    fake_entities = []

    # The following list and count are used to get an idea of the likely number
    # of random collisions:
    hrns_random_duplicates = []
    hrns_random_duplicates_count = 0

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
        if m:
            hrns_random_duplicates.append(m)
            hrns_random_duplicates_count += 1
        else:
            print("{:>4}".format(ec) + "\t", end="")
            ec += 1
            fake_entities.append([fph, hrns, e, m])

    #for i in range(hrns_random_duplicates_count):
    #    print(".", end="")

        #print(".", end="") # show indication of progress
    print()
    print()

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


# The set of fake entities is generated:
create_fake_entities(200)

#print("Fake entities initially in temporary lists:")
#list_l_entities()

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

print()
print("="*160)
print()

# The full set of fake entities is now listed, this time extracted from the
# (temporary) SQLite database:
with sqlite3.connect(ENTITIES_DB) as conn:
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM namespaces;")
    namespace_list = cursor.fetchall()
    print("\nnamespaces:\n")
    for namespace in namespace_list:
        print(namespace)

    cursor.execute("SELECT * FROM agents;")
    agent_list = cursor.fetchall()
    print("\nagents:\n")
    for agent in agent_list:
        print(agent)

    cursor.execute("SELECT * FROM currencies;")
    currency_list = cursor.fetchall()
    print("\ncurrencies:\n")
    for currency in currency_list:
        print(currency)

    cursor.execute("SELECT * FROM accounts;")
    account_list = cursor.fetchall()
    print("\naccounts:\n")
    for account in account_list:
        print(account)

    cursor.close()

    print()
    print("="*160)
    print()

#==============================================================================
# List each fake agent's accounts:

print("\nList the fake agents' accounts:\n")

for agent_fph in l_agents:
    print(agent_fph + " :: " + fph_to_hrns(agent_fph))
    accounts_fph_list, m = list_agent_accounts(agent_fph)
    if m:
        print("\t" + m)
    else:
        for account_fph in accounts_fph_list:
            print("\t" + fph_to_hrns(account_fph))
print()
print("="*160)

# List currencies to which each fake agent has an account:
print("\nList the fake agents' accounts' currencies:\n")

for agent_fph in l_agents:
    print(agent_fph + " :: " + fph_to_hrns(agent_fph))
    currencies_fph_list = list_agent_currencies(agent_fph)
    for currency_fph in currencies_fph_list:
        print("\t" + fph_to_hrns(currency_fph))
print()
print("="*160)

# List each fake currency's accounts:
print("\nList the fake currencies' accounts:\n")

for currency_fph in l_currencies:
    print(currency_fph + " :: " + fph_to_hrns(currency_fph))
    accounts_fph_list, m = list_currency_accounts(currency_fph)
    for account_fph in accounts_fph_list:
        print("\t" + account_fph + " :: " + fph_to_hrns(account_fph))

print()
print("="*160)
print()

print("Testing get_entity_type(entity_fph) function:")

print("\nNamespaces:")
for namespace_fph in l_namespaces:
    entity_type, m = get_entity_type(namespace_fph)
    print("\t" + fph_to_hrns(namespace_fph) + " (" + namespace_fph + ")", end="")
    if entity_type != "namespace":
        print(" misidentified as " + entity_type + " (" + m + ")")
    else:
        print(" identified correctly as " + entity_type)

print("\nCurrencies:")
for currency_fph in l_currencies:
    entity_type, m = get_entity_type(currency_fph)
    print("\t" + fph_to_hrns(currency_fph) + " (" + currency_fph + ")", end="")
    if entity_type != "currency":
        print(" misidentified as " + entity_type + " (" + m + ")")
    else:
        print(" identified correctly as " + entity_type)

print("\nAgents:")
for agent_fph in l_agents:
    entity_type, m = get_entity_type(agent_fph)
    print("\t" + fph_to_hrns(agent_fph) + " (" + agent_fph + ")", end="")
    if entity_type != "agent":
        print(" misidentified as " + entity_type + " (" + m + ")")
    else:
        print(" identified correctly as " + entity_type)

print("\nAccounts:")
for account_fph in l_accounts:
    entity_type, m = get_entity_type(account_fph)
    print("\t" + fph_to_hrns(account_fph) + " (" + account_fph + ")", end="")
    if entity_type != "account":
        print(" misidentified as " + entity_type + " (" + m + ")")
    else:
        print(" identified correctly as " + entity_type)

#==============================================================================
# The full set of fake entities is now listed againfrom the SQLite database:

with sqlite3.connect(ENTITIES_DB) as conn:
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM namespaces;")
    namespace_list = cursor.fetchall()
    print("\nnamespaces:\n")
    for namespace in namespace_list:
        print(namespace)

    cursor.execute("SELECT * FROM agents;")
    agent_list = cursor.fetchall()
    print("\nagents:\n")
    for agent in agent_list:
        print(agent)

    cursor.execute("SELECT * FROM currencies;")
    currency_list = cursor.fetchall()
    print("\ncurrencies:\n")
    for currency in currency_list:
        print(currency)

    cursor.execute("SELECT * FROM accounts;")
    account_list = cursor.fetchall()
    print("\naccounts:\n")
    for account in account_list:
        print(account)

    cursor.close()

print()
print("="*160)
print()

#==============================================================================
# Now that we have a usefully large collection of fake accounts, we can run
# some payment tests:

def test_payment_function():
    print("="*160)
    print("Testing payment function:\n")
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
            p_table.add_rows(p_rows[1:])
            print(p_table)



#test_payment_function()

def list_accounts(dtype="tuple"):
    # Now let's take another look at the accounts:
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM accounts;")
        account_list = list(cursor.fetchall())
        cursor.close()
    print("\naccounts:\n")

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


list_accounts("table")
#list_accounts()
test_payment_function()

list_accounts("table")
#list_accounts()



#==============================================================================
#

def show_payments_for_test_currencies():
    print("\nPayments in each currency\n")
    for currency_fph in l_currencies:
        print(currency_fph + " :: " + fph_to_hrns(currency_fph))
        dump_currency_payments(currency_fph)

#show_payments_for_test_currencies()




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

print("\nStewards\n")

for entity_fph in test_entities:
    print(fph_to_hrns(entity_fph))
    stewards, m = list_stewards(entity_fph)
    if m:
        print(m)
    for steward_fph in stewards:
        print(fph_to_hrns("\t" + steward_fph))

print("\nStewardships\n")

for agent_fph in test_agents:
    print(fph_to_hrns(agent_fph))
    stewardships, m = list_stewardships(agent_fph)
    if m:
        print(m)
    for entity_fph in stewardships:
        print("\t" + fph_to_hrns(entity_fph))

#remove_steward(entity_fph, agent_fph)
