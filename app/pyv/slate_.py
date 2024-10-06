#!/usr/bin/env python3
#
# This is a simple CLI tool for SLATE users.

import argparse



from slate_core import identify_entity



p = argparse.ArgumentParser(description="SLATE command line tool")
#
# Create new entities:
#
#p.add_argument(
#    "-A", "--create-account", dest = "account_hrns", action = "store",
#    help = "Create a new account with the specified HRNS. Always used with the"
#         + " -c option."
#)
#p.add_argument(
#    "-C", "--create-currency", dest = "currency_hrns", action = "store",
#    help = "Create a new currency with the specified HRNS, initially under the"
#         + "stewardship of the creating agent."
#)
#p.add_argument(
#    "-N", "--create-namespace", dest = "namespace_hrns", action = "store",
#    help = "Create a new namespace with the specified HRNS, initially under"
#         + " the stewardship of the creating agent."
#)
p.add_argument(
    "-N", "--create", dest = "entity_type", action = "store",
    options = ["account", "currency", "namespace"],
    help = "Create a new entity of the specified type (account, currency,"
         + " or namespace) with the HRNS specified in the first positional"
         + " argument. The agent creating the entity will be the owner (if an"
         + " account) or the initial steward (if a namespace or currency)."
         + " If the new entity is an account, the currency must be specified"
         + " (either by HRNS or FPH) either as the second positional argument"
         + " or by using the -c option."
)
#
p.add_argument(
    "entity_hrns", action = "store",
    help = "HRNS of new entity created"
)
#
p.add_argument(
    "payee_identifier", action = "store",
    help = "The HRNS or FPH of a payee account or agent."
)
#
p.add_argument(
    "-L", "--list", dest = "entity_type", action = "store",
    choices = ["accounts", "namespaces", "currencies"]
    help = "List all entities owned (accounts) or stewarded (namespaces or"
         + " or currencies) by this agent, i.e.\n"
         + "    -L accounts"
         + "    -L namespaces"
         + "    -L currencies"
         + "Unless a currency is specified using the -c option, '-L accounts'"
         + " causes all accounts to be listed."
)
#
# Specify the currency to be used with the -A or -L options (otherwise ignored):
#
p.add_argument(
    "-c", "--currency", dest = "currency_identifer", action = "store",
    help = "Specify the currency to be used in payment (-p), in the creation"
         + " of an account (-A) or in the listing of accounts (-L)."
)
#
# Payments:
#
p.add_argument(
    "-p", "--pay-account", dest = "account_identifier", action = "store",
    help = "Make a payment (of the amount specified using -a) to the account"
         + " identified by HRNS or FPH. In this case, the currency is"
         + " identified from the payer account. If the payee account specified"
         + " is not in the same currency, an error message is returned."
)
p.add_argument(
    "-P", "--pay-agent", dest = "agent_identifier", action = "store",
    help = "Make a payment (of the amount specified using -a) to the agent"
         + " identified by HRNS or FPH in the currency identified by '-c"
         + " <currency_identifier>'. If the payer and payee do not both have"
         + " an account in the same currency, an error message is returned."
)
#
#p.add_argument()
#p.add_argument()
#p.add_argument()
#p.add_argument()
#p.add_argument()
#p.add_argument()
#p.add_argument()
#p.add_argument()
#p.add_argument()
#
# The following may not be needed:
#
p.add_argument(
    "F", "--identify-by-fph", dest = "identify_by_fph",
    help = "Interpret entity identifiers as FPH. If not specified, the"
         + " identifier type will be identifed automatically.""
)
p.add_argument(
    "H", "--identify-by-hrns", dest = "identify_by_hrns",
    help = "Interpret entity identifiers as HRNS. If not specified, the"
         + " identifier type will be identifed automatically."
)
#
args = p.parse_args()

if
