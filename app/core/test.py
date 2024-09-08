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

from constants import ENTITIES_DB, PAYMENTS_DB, DB_DIR, FPH_TO_HRNS_MAP
from dbm_functions import dbm_list_entries
from slate_core import create_entities_db
from payments import create_payments_db
from slate_core import new_namespace, new_agent, new_currency, new_account
from slate_core import create_seed_entities
from fph_hrns_maps import hrns_to_fph, fph_to_hrns, create_maps
from slate_core import get_currency_name
from slate_core import list_agent_accounts
from slate_core import list_agent_currencies
from slate_core import list_currency_accounts
from common import nshash
from auth import auth_hash

# TEMPORARY TEST BITS

# Initialize Faker object
fake = Faker()
Faker.seed(24)

#
print("Please wait while a set of fake entities is created. ", end="")
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
    name_length = random.randint(3,5)
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
    return random_hrns(random.randint(1,6))

# For the purposes of these tests, a list of each randomly-generated entity is
# saved in a list, starting with the "seed" entities' FPH:
l_namespaces = [nshash("global")]           # seed namespace "global"
l_currencies = [nshash("hours.global")]     # seed currency "hours.global"
l_agents = [nshash("gaia.global")]          # seed agent "gaia.global"
l_accounts = [nshash("hours.gaia.global")]  # seed account "hours.gaia.global"

def list_entities():
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
#list_entities()


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

def record_test_agent_credentials(fph, hrns, password, pin):
    agent_credentials[fph] = [hrns, password, pin]

def get_test_agent_hrns(fph):
    return agent_credentials[fph][0]

def get_test_agent_password(fph):
    return agent_credentials[fph][1]

def get_test_agent_pin(fph):
    return agent_credentials[fph][2]


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

    agent_fph, agent_hrns, m = new_agent(
                                   agent_name,
                                   parent_namespace_fph,
                                   agent_realname,
                                   agent_email,
                                   password,
                                   pin,
                                   initial_currency_fph,
                                   initial_stewardship_fph_list
                               )

    agent_credentials[agent_fph] = [agent_hrns, password, pin]

    l_agents.append(agent_fph)

    return agent_fph, agent_hrns, m


def create_test_currency():

    parent_namespace_fph = select_available_namespace()
    #currency_name = random_name()
    currency_name = random.choice([
                        "hours",
                        "energy",
                        "gpounds",
                        "gdollars"
                    ])
    if currency_name == "hours":
        currency_prefix = ""
        currency_suffix = "h"
    elif currency_name == "energy":
        currency_prefix = ""
        currency_suffix = "kWh"
    elif currency_name == "gpounds":
        currency_prefix = "G£"
        currency_suffix = ""
    elif currency_name == "gdollars":
        currency_prefix = "G$"
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

    return account_fph, account_hrns, m


#==============================================================================
# A set of fake entities is created, each built upon a set of randomly-selected
# entities satisfying the dependency requirements:

def create_fake_entities(n):

    fake_entities = []

    # The following list and count are used to get an idea of the likely number
    # of random collisions:
    hrns_random_duplicates = []
    hrns_random_duplicates_count = 0

    for i in range(n):
        # Create a new entity the type of which is selected randomly and the
        # dependencies of which exist only among those already created:
        e = random.choice(["namespace", "agent", "currency", "account"])
        #print("Creating a new " + e + ":  ", end="")
        if e == "namespace":
            fph, hrns, m = create_test_namespace()
            if m:
                hrns_random_duplicates.append(m.replace(" exists", ""))
                hrns_random_duplicates_count += 1
            else:
                fake_entities.append([fph, hrns, e, m])
        elif e == "agent":
            fph, hrns, m = create_test_agent()
            if m:
                hrns_random_duplicates.append(m.replace(" exists", ""))
                hrns_random_duplicates_count += 1
            else:
                fake_entities.append([fph, hrns, e, m])
        elif e == "currency":
            fph, hrns, m = create_test_currency()
            if m:
                hrns_random_duplicates.append(m.replace(" exists", ""))
                hrns_random_duplicates_count += 1
            else:
                fake_entities.append([fph, hrns, e, m])
        elif e == "account":
            fph, hrns, m = create_test_account()
            if m:
                hrns_random_duplicates.append(m.replace(" exists", ""))
                hrns_random_duplicates_count += 1
            else:
                fake_entities.append([fph, hrns, e, m])
        else:
            print("Something has gone very wrong here")


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


# The fake agents are listed (along with their login credentials) from the
# temporary list:
def list_fake_agents():
    fa_rows = []
    for key in agent_credentials.keys():
        agent = agent_credentials[key]
        agent.insert(0, key)
        fa_rows.append(agent)
    fa_table = PrettyTable()
    fa_table.field_names = ["agent FPH", "agent HRNS", "password", "PIN"]
    fa_table.align = "l"
    fa_table.add_rows(fa_rows[1:])
    print(fa_table)


list_fake_agents()

print()
print("="*80)
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
    print("="*80)
    print()

#==============================================================================
# List each fake agent's accounts:

print("\nList the fake agents' accounts:\n")

for agent_fph in l_agents:
    print(agent_fph + " :: " + fph_to_hrns(agent_fph))
    accounts_fph_list = list_agent_accounts(agent_fph)
    for account_fph in accounts_fph_list:
        print("\t" + fph_to_hrns(account_fph))
print()
print("="*80)
print()

# List currencies to which each fake agent has an account:
print("\nList the fake agents' accounts' currencies:\n")

for agent_fph in l_agents:
    print(agent_fph + " :: " + fph_to_hrns(agent_fph))
    currencies_fph_list = list_agent_currencies(agent_fph)
    for currency_fph in currencies_fph_list:
        print("\t" + fph_to_hrns(currency_fph))
print()
print("="*80)
print()


#for i in range(10):
#    print()
#    no_common_currency_found = True
#    while no_common_currency_found:
#        agent_fph = select_available_agent()
#        currency_fph = select_available_currency()
#        no_
#        while



#    print("agent\t= " + fph_to_hrns(agent_fph))
#    print("currency\t= " + fph_to_hrns(currency_fph))
#    accounts_fph_list = list_currency_accounts(agent_fph, currency_fph)
#    for account_fph in accounts_fph_list:
#        print("\t" + fph_to_hrns(account_fph))
#    print()




#==============================================================================
# Now that we have a usefully large collection of fake accounts, we can run
# some payment tests:
