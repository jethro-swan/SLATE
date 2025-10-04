#!/home/slate/SLATE/venv/bin/python3

from app.core.fph_hrns_maps import fph_to_hrns
from app.core.fph_hrns_maps import hrns_to_fph

from app.core.constants import GRAPHS

from app.core.common import filename_timestamp

from app.core.slate_core import list_ahids
from app.core.slate_core import list_ahid_accounts
from app.core.slate_core import get_account_currency
from app.core.slate_core import get_account_properties
from app.core.slate_core import identify_entity
from app.core.slate_core import list_currency_accounts
from app.core.slate_core import retrieve_pairing_account_fph as pairing_account

from app.core.exports import list_payments_in_currency

import math




h_len = 400
v_len = 400
h_offset = h_len/2
v_offset = v_len/2



svg_head = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>" \
         + "<svg width=\"" + str(h_len) + "\" height=\"" + str(v_len) + "\">"
svg_foot = "</svg>"




#N = 3
#circ = math.pi * 2
#arc = circ/N
#r = 190


ahid_account_list = []

accounts = {}
number_of_accounts = 0 # increased by 1 for each *ahid* found



def _accounts_circle(currency_id):
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not currency_fph:
        return {}, "Identifier " + currency_id + " is not registered"
    if not ("currency" in etypes):
        return {}, "Identifier " + currency_hrns + " has no currency registered"

    payments_list, m = list_payments_in_currency(currency_id)
    accounts_fph_list = list_currency_accounts(currency_fph)
    # The *accounts* will be plotted as equally-spaced points on a circle.
    # For a modest number of *accounts* (suitable for display in a simpled SVG
    # circle plot) their coordinates are recorded in a dictionary using the
    # *account* FPH as a key.
    A = {}
    N = len(accounts_fph_list)
    circ = math.pi * 2
    arc = circ/N
    r = 190 # radius within 400x400 square
    n = 0
    for account_fph in accounts_fph_list: # N *accounts*
        currency_fph, owner_fph, account_balance, account_volume, active, \
        account_type, account_category, account_units, \
        account_metrical_equivalence, account_dimensions, \
        m = get_account_properties(account_fph)
#        owner_fph, owner_hrns, etypes, m = identify_entity(owner_fph)
#        if ("ahid" in etypes) and ("account" in etypes):
#            continue
        p = {}
        # The *ahid* coordinate on the circle
        a = n * arc
        p["x"] = r * math.sin(a)
        p["y"] = r * math.cos(a)
        p["balance"] = account_balance
        p["volume"] = account_volume
        p["owner"] = owner_fph # *ahid* FPH
#        A[account_fph] = p
#        print(owner_fph + " <> " + fph_to_hrns(owner_fph))
#        A[owner_fph] # *ahid* FPH
        n += 1
    return A, ""



def _plot_accounts_circle(currency_id):
    # Each dot in the plot represents an *account*. Since each *account* is
    # identified by a *currency*|*ahid* pairing and the *currency* has been
    # specified, each dot in the plot represents an *ahid*.
    #
    # (1) Prepare to place dots in a circle to represent *accounts*.
    A, m = accounts_circle(currency_id)
    h_len = 400
    v_len = 400
    h_shift = str(h_len/2)
    v_shift = str(v_len/2)
    #
    # (2) The list of payments in this *currency* is retrieved.
    payments_list, m = list_payments_in_currency(currency_id)
    for row in payments_list:
        print("from " + row[2] + " to " + row[3] + " in " + row[4])
#    print(payments_list)
    #
    with open(GRAPHS + "ahid_circle.svg", "w") as ac:
        ac.write(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        )
        ac.write(
            "<svg width=\"" + str(h_len) + "\" height=\"" + str(v_len) + "\"" \
            + " viewbox=\"0 0 400 400\" xmlns=\"http://www.w3.org/2000/svg\">"
        )
        # First the dots are drawn:
        for ahid_fph in A:
            ac.write(
                "\n<circle cx=\"" + str(A[ahid_fph]["x"]) \
                + "\" cy=\"" + str(A[ahid_fph]["y"]) \
                + "\" r=\"" + str(4) + "\" " \
                + "style=\"stroke-width:1;stroke:black;fill:black;\" " \
                + "transform=\"translate(200,200)\"/>"
            )
        # Then the payments between *accounts* are drawn in:
        for p in payments_list:
            payer_ahid_fph, m = hrns_to_fph(p[2])
            payee_ahid_fph, m = hrns_to_fph(p[3])
            payer_account_fph, primid_fph, \
            m = pairing_account(payer_ahid_fph, currency_id)
            payee_account_fph, primid_fph, \
            m = pairing_account(payer_ahid_fph, currency_id)

#            x1 = A[payer_account_fph]["x"]
#            y1 = A[payer_account_fph]["y"]
#            x2 = A[payee_account_fph]["x"]
#            y2 = A[payee_account_fph]["y"]
            x1 = A[payer_ahid_fph]["x"]
            y1 = A[payer_ahid_fph]["y"]
            x2 = A[payee_ahid_fph]["x"]
            y2 = A[payee_ahid_fph]["y"]

#            print(
#                "(x1, y1) = (" + str(x1 + 200) + ", " + str(y1 + 200) + ")\n" \
#                "(x2, y2) = (" + str(x2 + 200) + ", " + str(y2 + 200) + ")\n"
#            )

            ac.write(
                '\n<line ' \
                + 'x1="' + str(x1) + '" y1="' + str(y1) + '" ' \
                + 'x2="' + str(x2) + '" y2="' + str(y2) + '" ' \
                + 'style="stroke:green;stroke-width:3;" ' \
                + 'transform="translate(200,200)"/>'
            )

        ac.write("\n</svg>")


def accounts_circle(currency_id):
    currency_fph, currency_hrns, etypes, m = identify_entity(currency_id)
    if not currency_fph:
        return "Identifier " + currency_id + " is not registered"
    if not ("currency" in etypes):
        return "Identifier " + currency_hrns + " has no currency registered"
    payments_list, m = list_payments_in_currency(currency_id)
    ahids_fph_list = []
    for row in payments_list:
        payer_ahid_fph = row[2]
        payee_ahid_fph = row[3]
        print("from " + row[2] + " to " + row[3] + " in " + row[4])
        if not (payer_ahid_fph in ahids_fph_list):
            ahids_fph_list.append(payer_ahid_fph)
        if not (payee_ahid_fph in ahids_fph_list):
            ahids_fph_list.append(payee_ahid_fph)
    # The *ahid*s will be plotted as equally-spaced points on a circle.
    # For a modest number of *ahid*s (suitable for display in a simpled SVG
    # circle plot) their coordinates are recorded in a dictionary using the
    # *ahid* FPH as a key.
    A = {}
    N = len(ahids_fph_list)
    circ = math.pi * 2
    arc = circ/N
    r = 190 # radius within 400x400 square
    n = 0
    for ahid_fph in ahids_fph_list: # N *ahids*
        p = {}
        # The *ahid* coordinate on the circle
        a = n * arc
        p["x"] = r * math.sin(a)
        p["y"] = r * math.cos(a)
        n += 1

    # Each dot in the plot represents an *account*. Since each *account* is
    # identified by a *currency*|*ahid* pairing and the *currency* has been
    # specified, each dot in the plot represents an *ahid*.
    #
    # (1) Prepare to place dots in a circle to represent *accounts*.
    h_len = 400
    v_len = 400
    h_shift = str(h_len/2)
    v_shift = str(v_len/2)
    #
    # (2) The list of payments in this *currency* is retrieved.
    for row in payments_list:
        print("from " + row[2] + " to " + row[3] + " in " + row[4])
    #
    with open(GRAPHS + "ahid_circle.svg", "w") as ac:
        ac.write(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
        )
        ac.write(
            "<svg width=\"" + str(h_len) + "\" height=\"" + str(v_len) + "\"" \
            + " viewbox=\"0 0 400 400\" xmlns=\"http://www.w3.org/2000/svg\">"
        )
        # First the dots are drawn:
        for ahid_fph in A:
            ac.write(
                "\n<circle cx=\"" + str(A[ahid_fph]["x"]) \
                + "\" cy=\"" + str(A[ahid_fph]["y"]) \
                + "\" r=\"" + str(4) + "\" " \
                + "style=\"stroke-width:1;stroke:black;fill:black;\" " \
                + "transform=\"translate(200,200)\"/>"
            )
        # Then the payments between *accounts* are drawn in:
        for p in payments_list:
            payer_ahid_fph, m = hrns_to_fph(p[2])
            payee_ahid_fph, m = hrns_to_fph(p[3])
            payer_account_fph, primid_fph, \
            m = pairing_account(payer_ahid_fph, currency_id)
            payee_account_fph, primid_fph, \
            m = pairing_account(payer_ahid_fph, currency_id)

            x1 = A[payer_ahid_fph]["x"]
            y1 = A[payer_ahid_fph]["y"]
            x2 = A[payee_ahid_fph]["x"]
            y2 = A[payee_ahid_fph]["y"]

            ac.write(
                '\n<line ' \
                + 'x1="' + str(x1) + '" y1="' + str(y1) + '" ' \
                + 'x2="' + str(x2) + '" y2="' + str(y2) + '" ' \
                + 'style="stroke:green;stroke-width:3;" ' \
                + 'transform="translate(200,200)"/>'
            )

        ac.write("\n</svg>")

    return ""






# The following information is gathered:
# (1) all the *ahid*s to/from which one of this *primid*'s *ahid*s can
#     make/receive a payment;
# (2) all the *currencies* in which such payments might be made; and
# (3) all the *ahid*s

def list_all_reachable_accounts(primid_fph):
    reachable_ahids = []
    # Start by listing all *ahid*s belong to this *primid*:
    ahid_fph_list = list_ahids(primid_fph)
    for ahid_fph in ahid_fph_list:
        # If this *ahid* has not yet been added to the dictionary, an empty
        # sub-dictionary is created for it:
        if not (ahid_fph in accounts.keys()):
            accounts[ahid_fph] = {}
        # Now we need to know with which *currencies* have a pairing with each
        # of these *ahid*s:
        ahid_account_fph_list = list_ahid_accounts(ahid_fph)
        for account_fph in ahid_account_fph_list:
            currency_fph, m = get_account_currency(account_fph)
            # For each of these *currencies*, we need to list all the
            # *accounts*:
            all_accounts_fph_list = list_currency_accounts(currency_fph)
            for account_fph in all_accounts_fph_list:
                currency_fph, owner_fph, balance, volume, active, \
                account_type, account_category, account_units, \
                account_metrical_equivalence, account_dimensions, \
                m = get_account_properties(account_fph)
                if not (owner_fph in reachable_ahids):
                    reachable_ahids.append(owner_fph)
