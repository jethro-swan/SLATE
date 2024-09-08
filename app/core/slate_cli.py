#!/usr/bin/env python3
# Linked to from SLATE/CLI/slate_pay
#
# This is a command line payment script, generally invoked over SSH.

import sys

from app.core import slate_core

script_name = sys.argv[0].replace("./", "").replace(".py", "")

if script_name == "slate_pay":
    if len(sys.argv) != 5:
        sys.stderr.write("Too few arguments")
        sys.exit(1)
    payer_fph   = sys.argv[1]
    payee_fph   = sys.argv[2]
    payment     = sys.argv[3]
    annotation  = sys.argv[4]
    response = payment(payer_fph, payee_fph, payment, annotation)
    sys.stderr.write(response)
    sys.exit(0)

if script_name == "slate_currency_report":
    if len(sys.argv) != 2:
        sys.stderr.write("Too few arguments")
        sys.exit(1)
    currency_fph = sys.argv[1]
    response = currency_report(currency_fph)
    print(response)
    sys.exit(0)

if script_name == "slate_account_report":
    if len(sys.argv) != 2:
        sys.stderr.write("Too few arguments")
        sys.exit(1)
    account_fph = sys.argv[1]
    response = account_report(account_fph)
    print(response)
    sys.exit(0)

if script_name == "slate_agent_new":
    if len(sys.argv) != 7:
        sys.stderr.write("Too few arguments")
        sys.exit(1)
    agent_hrns = sys.argv[1]
    currency_fph = sys.argv[2]      # initial currency
    agent_name = sys.argv[3]        # (optional)
    agent_email = sys.argv[4]
    agent_password = sys.argv[5]    # required
    agent_pin = sys.argv[6]         # required
    agent_fph = hrns_to_fph(agent_hrns)
    response = create_agent(agent_hrns, agent_fph, agent_email, currency_fph,
                            agent_name, agent_password, agent_pin
               )
    print(agent_fph)
    print(response)
    sys.exit(0)

if script_name == "slate_agent_update":
    if len(sys.argv) != 6:
        sys.stderr.write("Too few arguments")
        sys.exit(1)
    agent_hrns = sys.argv[1]
    currency_fph = sys.argv[2]      # additional currency (if provided)
    agent_name = sys.argv[3]        # (optional) changed if provided
    agent_password = sys.argv[4]    # (optional) changed if provided
    agent_pin = sys.argv[5]         # (optional) changed if provided
    print(agent_fph)
    print(response)
    sys.exit(0)
