#!/home/slate/SLATE/venv/bin/python3

import sqlite3
import pickle
import random

import sys, os, re, argparse


from app.core.fph_hrns_maps import fph_to_hrns, hrns_to_fph

from app.core.slate_core import new_namespace, new_currency, new_primid
from app.core.slate_core import split_hrns

from app.core.slate_core import new_pairing
from app.core.slate_core import retrieve_pmap
from app.core.slate_core import complete_parent_namespace
from app.core.payments import ah_payment


#==============================================================================
# Set command line options:

ap = argparse.ArgumentParser(description = "Create a random payment set")
ap.add_argument(
    "-p", "--primid", dest = "primid_id", action = "store",
    help = "Login identity of user"
)
ap.add_argument(
    "-n", "--number-of-payments", dest = "n_payments", action = "store",
    default = 100,
    help = "Number of payments"
)
ap.add_argument(
    "-c", "--currency", dest = "currency_id", action = "store",
    help = "Currency"
)
ap.add_argument(
    "-a", "--ahid-prefix", dest = "ahid_prefix",  action = "store",
    default = "a",
    help = "Prefix for AHID identifiers"
)
ap.add_argument(
    "-A", "--number-of-ahid", dest = "number_of_ahid",  action = "store",
    default = 10,
    help = "The number of AHIDs to be created"
args = ap.parse_args()

primid_id = args.primid_id
#if args.n_payments is not None:
#    n_payments = args.n_payments
n_payments = args.n_payments
currency_id = args.currency_id
ahid_prefix = args.ahid_prefix
number_of_ahid = args.number_of_ahid

primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
if not primid_fph:
    sys.stderr.write("Specified primid does not exist")
    sys.exit(1)

currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
if not currency_fph:
    sys.stderr.write("Specified currency does not exist")
    sys.exit(1)

ahid_hrns_list = []
for i in range(number_of_ahid):
    ahid_hrns_list.append(ahid_prefix + str(i) + "." + primid_hrns)

for ahid_hrns in ahid_hrns_list:
    p_fph = new_pairing(primid_id, ahid_hrns, currency_hrns)

pmap, m = retrieve_pmap(primid_hrns)

run_payment_test_loop = True

display_random_selection = True

if test_entity_identification:
    for ahid_hrns in ahid_hrns_list:
        ahid_fph, ahid_hrns, etypes, m = identify_entity(ahid_hrns)
        if m:
            print(m)
        if not ahid_fph:
            print(ahid_fph + " is not a registered identifier (18)")
        elif not ("ahid" in etypes):
            print(ahid_hrns + " has no registered ahid")
        print(etype + ": " + ahid_fph + " > " + ahid_hrns)

if run_payment_test_loop:
    print("="*80)
    print("Running payment test loop")
    print("-"*80)
    for n in range(n_payments):
        payer_ahid_hrns = random.choice(ahid_hrns_list)
        payee_ahid_hrns = random.choice(ahid_hrns_list)
        currency_hrns = random.choice(currency_hrns_list)
        amount = random.randint(0, 100000)
        annotation = "test B" + str(n).zfill(4)
        if payer_ahid_hrns != payee_ahid_hrns:
            if display_random_selection:
                print(
                    currency_hrns + " : " \
                    + payer_ahid_hrns + " > " + payee_ahid_hrns \
                    + " | " + str(amount) \
                    + " | " + annotation
                )
            if test_payments:
                m = ah_payment(
                        payer_ahid_hrns,
                        payee_ahid_hrns,
                        currency_hrns,
                        amount,
                        annotation
                    )
                if m:
                    print(m)
    print("="*80)
