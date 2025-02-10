## CSV import tools

These tools are used on the command line for bulk actions.

They include:

#### Namespaces

- tools/pyv/slate_import_namespaces.py
- tools/slate_import_namespaces
- /usr/local/bin/slate_import_namespaces

name:parent namespace:initial steward:default currency

e.g. "gc":"chep.mon.uk":"jw.chep.mon.uk":"hrs.chep.mon.uk"

#### Currencies

- tools/pyv/slate_import_currencies.py
- tools/slate_import_currencies
- /usr/local/bin/slate_import_currencies

name:parent namespace:initial steward:prefix:suffix:default account name

e.g. "hrs":"chep.mon.uk":"jw.chep.mon.uk":"":"h":"hrs"

#### Accounts

- tools/pyv/slate_import_accounts.py
- tools/slate_import_accounts
- /usr/local/bin/slate_import_accounts

account name:parent namespace:owner:currency

e.g. "kwh":"jw.gc.chep.mon.uk":"jw.chep.mon.uk":"kwh.gc.chep.mon.uk"

#### Aliases

- tools/pyv/slate_import_aliases.py
- tools/slate_import_aliases
- /usr/local/bin/slate_import_aliases

name:parent namespace:login identity

e.g. "js":"global.cc":"jw.gc.chep.mon.uk"

#### Primary identities (a.k.a login identities)

- tools/pyv/slate_import_primids.py
- tools/slate_import_primids
- /usr/local/bin/slate_import_primids

name:parent namespace:real name:email1:email2:password:PIN

e.g. "fred":gc.chep.mon.uk":"":"fred@dodgy.com":"":"bAdpA55w0rd":"314159"

NB, optional fields (such as the user's real name or the second recovery email
address) can be left as empty strings, as in this example.

#### Payments

- tools/pyv/slate_import_payments.py
- tools/slate_import_payments
- /usr/local/bin/slate_import_payments

payer account:payee account:amount:annotation

e.g. "ab.cd.de":"fg.hi.jk.lm":"543.21":"Some reason"

---

Such CSV files can be created easily using spreadsheet software (e.g.
LibreOffice Calc).

#### Use on the command line

e.g.

    cat namespaces_list.csv | slate_import_namespaces

#### Usage over SSH:

e.g. running on the user's command line (locally):

    cat accounts.csv | ssh -p port user@server_url slate_import_accounts

Where
- **user**	is the user's SSH login identity
- **server_url** is the address of the server
- **port** is port number (generally forwarded to a VM running SLATE instance)
- **accounts.csv** is a CSV file containing the details to create a set of
**accounts**
- **slate_import_accounts** is the script that parses the CSV file to create a
set of **accounts**

This means that the CSV file does not need to be uploaded to the server.
