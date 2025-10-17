#!/home/slate/SLATE/venv/bin/python3

import random
import math




h_len = 400
v_len = 400
h_offset = h_len/2
v_offset = v_len/2


n_currencies = 5
n_agents = 25

pmax = 100 # maximum payment
rmax = 35 # maximim percentage payable in green

def create_simple_set():

    # The number of payments made or received by each agent used is used to
    # establish the vertical scaling.
    n_payments = []
    for a in range(n_agents):
        n_payments = 0

    # Initialize balances:
    bal_worst = []  # The balances in blue if it were the only option.
    for a in range(n_agents):
        bal_worst.append(0)
    bal_lt = []     # The legal tender balance for each agent.
    for a in range(n_agents):
        bal_lt.append(0)
    bal = []        # The CC (green) balance for each currency|agent pair.
    for c in range(n_currencies):
        bal.append([])
        for a in range(n_agents):
            bal[c].append(0)

    # The balances are shown in array of coloured bars - one for blue (LT) and
    # one for each of the community currencies (green). The green bars will
    # oscillate about 0 while the blue bars continue to grow negative with
    # each iteration.

    # An additional bar shows how far the blue would have "leaked" without the
    # green component.

    journal = [] # one journal per currency per agent
    for c in range(n_currencies):
        journal.append([])
        for a in range(n_agents):
            journal[c].append([])

    return bal_worst, bal_lt, bal, journal # initial values


def one_iteration(bal_worst, bal_lt, bal, journal):

    payer = random.randint(0, n_agents-1)
    print("payer: " + str(payer))
    payee = random.randint(0, n_agents-1)
    print("payee: " + str(payee))
    currency = random.randint(0, n_currencies-1)
    print("currency: " + str(currency))
    amount = random.randint(0, pmax)

    # The percentage green accepted is assumed to change with each purchase:
    #
    P = random.randint(0, rmax*10)/1000 # percentage to one decimal place
    amount_lt = amount * (1 - P)
    amount_cc = amount * P

    bal_worst[payee] += amount          # worst case blue (LT)
    bal_worst[payer] -= amount          #

    bal_lt[payee] += amount_lt          # blue (LT) balance
    bal_lt[payer] -= amount_lt          #

    bal[currency][payee] += amount_cc   # green (CC) balance
    bal[currency][payer] -= amount_cc   #

    # The updated balances are appended to the appropriate journals:
#    if not (currency in journal):
#        journal.append(currency)
    if not (payer in journal[currency]):
        journal[currency].append(payer)
    if not (payee in journal[currency]):
        journal[currency].append(payee)
    journal[currency][payer].append(bal[currency][payer])
    journal[currency][payee].append(bal[currency][payee])
    journal[0][payee].append(bal_lt[payee])

    return bal_worst, bal_lt, bal, journal


def all_iterations(n_iterations, bal_worst, bal_lt, bal, journal):

    for n in range(n_iterations):

        bal_worst, \
        bal_lt, \
        bal, \
        journal = one_iteration(bal_worst, bal_lt, bal, journal)

    return bal_worst, bal_lt, bal, journal
