# SLATE
# Last modified: 2024-08-22 00:05 JW

import os
from pathlib import Path
import re
import time
import sys

from common import filename_timestamp

# CSV can mean either "comma-separated value" or "character-separated value".
# Here the latter meaning is use, with a comma used as the default separator.

#------------------------------------------------------------------------------
# Each time a transaction is processed, an entry is written to the transaction
# record of both the account(s) and the currency. These transaction records are
# of a similar form but differ slightly.
#
# In an account's transaction record
# - The "target account" always refers to the account to which the transaction
#   record belongs.
# - The "other account" always refers to the account affected, whether that of
#   the payer or the payee.
#
# In a currency's transaction record, the payer account and payee account are
# identified as such.
#
# Where the currency is a local money type, two accounts are involved and the
# transaction is a payment. This is a special case of transaction (but probably
# likely to be the most common).

# SEPARATE THE FOLLOWING INTO ACCOUNT EXPORT AND CURRENCY EXPORT:
# An account history will contain
#   DATE, FROM|TO (FPH), AMOUNT, REASON
# i.e. a record of the flow around this network.
#
# Each line in a currency history will contain
#   DATE, FROM (FPH), TO (FPH), AMOUNT, REASON
# i.e. a record of the fluctuations within this network.


def v2dp(integer_string):
    return f"{int(integer_string)/100:.2f}"

def export_account_journal_to_csv(account_fph, sc=","):
    # NB, this is for exporting a list of payments, balances, etc., where the
    #     transaction type is payment (local money systems) only. Compound
    #     currency types require a somewhat more involved process.
    #
    #   account_<account_FPH>_transaction_history_<YYYYMMDDhhmmss>.csv

    entity_type = get_entity_type(account_fph)
    if (entity_type == "account"):
        currency_fph = get_account_currency(account_fph)
        currency_type = get_currency_type(currency_fph)
        output_filename = "account_"
    if not (currency_type = "money"):
        return "Cannot export for non-money types."
    output_filename += "account_" + account_fph + "_transaction_history_" \
                    + filename_timestamp() + ".csv"
    csv_f = open(NESTS_EXPORT + output_filename, "w")
    # The first line of the CSV output identifies the fields:
    write(csv_f, "date" + sc)                       # date
    write(csv_f, "time" + sc)                       # time
    write(csv_f, "flow" + sc)                       # debit|credit
    write(csv_f, "transaction number" + sc)         # transaction number
    write(csv_f, "other account FPH" + sc)          # FPH of other account
    write(csv_f, "other account HRN" + sc)          # HRN of other accoun
    write(csv_f, "amount" + sc)                     # amount paid|received
    write(csv_f, "balance" + sc)                    # balance of account
    write(csv_f, "annotation\n")                    # string
    dpath = fph_to_dpath(account_fph)
    with open(dpath + "/.history", "r") as tr_f:
        while tr_line = tr_f.readline():
            tr = r_line.split("|")
            write(csv_f, tr[0] + sc)                # date
            write(csv_f, tr[1] + sc)                # time
            write(csv_f, tr[3] + sc)                # debit|credit
            write(csv_f, tr[4] + sc)                # transaction number
            write(csv_f, tr[5] + sc)                # FPH of other account
            write(csv_f, fph_to_hrns(tr[5]) + sc)   # HRN of other account
            write(csv_f, v2dp(tr[6]) + sc)          # amount
            write(csv_f, v2dp(tr[7]) + sc)          # balance
            write(csv_f, tr[8] + "\n")              # annotation
    csv_f.close()
    return output_filename

#------------------------------------------------------------------------------
def export_currency_journal_to_csv(currency_fph, sc=","):
    # NB, this is for exporting a list of payments, balances, etc., where the
    #     transaction type is payment (local money systems) only. Compound
    #     currency types require a slightly more involved process.
    #
    #   currency_<currency_FPH>_transaction_history_<YYYYMMDDhhmmss>.csv

    entity_type = get_entity_type(currency_fph)
    if (entity_type == "account"):
        currency_fph = get_account_currency(currency_fph)
        currency_type = get_currency_type(currency_fph)
        output_filename = "account_"
    if not (currency_type = "money"):
        return "Cannot export for non-money types."
    output_filename += "account_" + currency_fph + "_transaction_history_" \
                    + filename_timestamp() + ".csv"
    csv_f = open(NESTS_EXPORT + output_filename, "w")
    # The first line of the CSV output identifies the fields:
    write(csv_f, "date" + sc)                       # date
    write(csv_f, "time" + sc)                       # time
    write(csv_f, "transaction number" + sc)         # transaction number
    write(csv_f, "payer account FPHS" + sc)         # payer account FPH
    write(csv_f, "payee account FPHS" + sc)         # payee account FPH
    write(csv_f, "payer account HRNS" + sc)         # payer account HRNS
    write(csv_f, "payee account HRNS" + sc)         # payee account HRNS
    write(csv_f, "amount" + sc)                     # integer
    write(csv_f, "annotation\n")                    # string
    dpath = fph_to_dpath(currency_fph)
    with open(dpath + "/.history", "r") as tr_f:
        while tr_line = tr_f.readline():
            tr = r_line.split("|")
            write(csv_f, "\"" + tr[0] + "\"" + sc)  # date of transaction
            write(csv_f, "\"" + tr[1] + "\"" + sc)  # time of transaction
            write(csv_f, "\"" + tr[3] + "\"" + sc)  # transaction number
            write(csv_f, "\"" + tr[4] + "\"" + sc)  # payer account FPH
            write(csv_f, "\"" + tr[5] + "\"" + sc)  # payee account FPH
            write(csv_f, fph_to_hrns(tr[4]) + sc)   # payer account HRNS
            write(csv_f, fph_to_hrns(tr[5]) + sc)   # payee account HRNS
            write(csv_f, v2dp(tr[5]) + sc)          # amount
            write(csv_f, tr[4] + "\n")              # annotation
    csv_f.close()
    return output_filename

#------------------------------------------------------------------------------
# Export a CSV report of all accounts using this currency:

def export_accounts_csv(fph): # FPH
    out_file = "currency_" + fph + "_export_" + filename_timestamp() + ".csv"
    if get_entity_type(currency_fph) != "currency":
        return False, currency_fph + " is not a currency"
    with open(CSV + "/" + out_file, "w") as out_f:
        out_f.write("account FPH;account HRNS;account balance")
        dpath = fph_to_dpath(currency_fph)
        with open(dpath, "r") as accounts_f:
            for account_fph in accounts_f:
                out_f.write(account_fph + ";")
                out_f.write(fph_to_hrns(account_fph) + ";")
                out_f.write(get_account_balance(account_fph) + "\n")
    return True, CSV + "/" + out_file # path to CSV export file

#------------------------------------------------------------------------------
# Export an HTML report of all accounts using this currency:

def list_accounts_csv(currency_fph): # FPH
    out_file = "currency_" + fph + "_report_" + filename_timestamp() + ".html"
    if get_entity_type(currency_fph) != "currency":
        return False, currency_fph + " is not a currency"
    with open(WWW + "/" + out_file, "w") as out_f:
        out_f.write('<!doctype html>\n<html language="en">\n')
        out_f.write('<head>')
        out_f.write('<title>currency report: ' + fph + '</title>\n')
        out_f.write('<link rel="stylesheet" type="text/css" ')
        out_f.write('href="css/locus.css">\n')
        out_f.write('<meta charset="UTF-8" />\n')
        out_f.write('</head>')

        out_f.write('<body class="report_header">\n')

        out_f.write('<table class="report_table">\n')
        out_f.write('<tr valign="top" class="report_table">\n')
        out_f.write('<th>account FPH</th>')
        out_f.write('<th>account HRNS</th>')
        out_f.write('<th>account balance</th>')
        out_f.write('</tr>')
        dpath = fph_to_dpath(currency_fph)
        with open(dpath, "r") as accounts_f:
            for acc_fph in accounts_f:
                out_f.write('<tr valign="top" class="report_table">\n')
                out_f.write('<td>' + acc_fph + '</td>')
                out_f.write('<td>' + fph_to_hrns(acc_fph) + '</td>')
                out_f.write('<td>' + get_account_balance(acc_fph) + "</td>\n")
                out_f.write('</tr>')
        out_f.write('</table>')
        out_f.write('</body>')
        out_f.write('</html>')
    return WWW + "/" + out_file # path to HTML export file

#------------------------------------------------------------------------------














#------------------------------------------------------------------------------
