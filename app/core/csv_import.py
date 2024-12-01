import os
from pathlib import Path
import re
import time
import sys
import json

from regexp_list import re_fph
from common import fph_to_dpath, fph_to_hrns
from common import get_currency_fph
from common import hrns_to_fph, fph_to_hrns, fph_to_fip, fph_to_dpath
from common import hrns_to_dpath
from common import entity_type, account_currency, currency_accounts
from regexp_list import re_fph, re_hrns, re_email



#==============================================================================
# A set of *accounts* is created in the specified *namespace*, all belonging to
# the same *identity*.
#
# The *currency* and *namespace* are specified in the form used for uploading
# the CSV file.
#
def import_minimal_payment_set_as_csv(
        owner_identifier,
        currency_identifier,
        namespace_identifier,
        csv_file
    ):

    errors = ""

    namespace_fph, \
    namespace_hrns, \
    etype, \
    m = identify_entity(namespace_identifier)
    if m:
        errors += m + "\n"
        return [], errors
    if etype != "namespace":
        errors += namespace_identifier + " is not a namespace\n"
        return [], errors

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_identifier)
    if m:
        errors += m + "\n"
        return [], errors
    if etype != "currency":
        errors += currency_identifier + " is not a currency\n"
        return [], errors

    payments_made = []

    account_names = []
    with open(csv_file, "r") as f:
        while
        row = f.readline()
        payer_name = row[0]
        payee_name = row[1]
        amount = row[2]
        annotation = row[3]

        if payer_name in account_names:
            payer_fph, \
            payer_hrns, \
            etype, \
            m = identify_entity(payer_name + "." + )
            if m:
                errors += m + "\n"
                return [], errors
        else:
            payer_fph, \
            payer_hrns, \
            m = new_account(
                payer_name,
                namespace_fph,
                owner_fph,
                currency_fph
            )
            if m:
                errors += m + "\n"
                return [], errors
            account_names.append(payer_name)

        if payee_name in account_names:
            payee_fph, \
            payee_hrns, \
            etype, \
            m = identify_entity(payee_name + "." + )
            if m:
                errors += m + "\n"
                return [], errors
        else:
            payee_fph, \
            payee_hrns, \
            m = new_account(
                payee_name,
                namespace_fph,
                owner_fph,
                currency_fph
            )
            if m:
                errors += m + "\n"
                return [], errors
            account_names.append(payee_name)

        m = payment(payer_fph, payee_fph, amount, annotation)
        if m:
            errors += m + "\n"
            return [], errors

        paid = payer_hrns + ":" \
             + payee_hrns + ":" \
             + amount + ":" \
             + annotation
        payments_made.append(paid)

    return payments, ""

#==============================================================================









# THIS MUST BE MODIFIED EXTENSIVELY

# CSV can mean either "comma-separated value" or "character-separated value".
# Here the latter meaning is used, with a semicolon used as the separator.

#------------------------------------------------------------------------------
def import_currency_record_csv(currency_fph, separator=";"):
    # FPH of currency
    #
    # The imported list includes (in each line):
    # - date (optional - if omitted, current date is used)
    # - time (optional - if omitted, current time is used)
    # - payer account HRN
    # - payee account HRN
    # - amount
    # - annotation (optional)
    #
    # If either account does not exist it will be created if the identity
    # initiating the import is authorized to do so.
    #



    return






#------------------------------------------------------------------------------
# A set of entity definitions is imported as CSV, either into an existing data
# set or into a new one. For each entity specification line, the entities upon
# which it depends must either have been defined in earlier lines or have been
# in existence already. When importing into an new data set, the only entities
# available upon which to build will be those in the seed set.

def import_csv_entity_set(data_set, entity_definition_file):

    if not data_set_exists(data_set):
        create_data_set(data_set)
    select_data_set(data_set)








#==============================================================================
# 2023-08-15:
#
# The functions below were moved here from a (possibly) obsolete file mamed
# import_csv.py.

# A set of identities is created. The initial account specified for each must
# exist already.
#
# Both primary identities and secondary identities may be created here, but a
# secondary identity may only be created after its associated primary identity.
#
# The input fields are:
#
#   type        "primid"|"secid"
#   identity    <HRNS string>
#   primid      "" if type = primid, <HRNS string> if type = "secid"
#   currency    <HRNS string> (initial currency must exist already)
#   email       <email string>
#   password    <password string>
#   PIN         <PIN string>
#
def identities_bulk_creation(import_file):
    if not re_csv_filename.match(import_file):
        return ("Bad filename: " + import_file)
    valid_fieldnames = [
                         "type",
                         "identity",
                         "primid",
                         "currency",
                         "email",
                         "password",
                         "PIN"
                       ]
    bad_rows = []
    problems = []
    created = []
    with open(import_file, "r") as import_f:
        # Check that the column headers are correct:
        header_line = import_f.readline()
        field = header_line.split(",")
        for h in len(field):
            if not field[h] == valid_fieldnames[h]:
                return ("Bad column header: " + field[h])
        # The rest of the file is now read line by line:
        row = import_f.readline()
        col = row.split(",")
        if not ( \
                (col[0] == "primid") or (col[0] == "secid") \
                and re_hrns.match(col[1])
                and ((col[2] == "") or re_hrns.match(col[2])) \
                and re_hrns.match(col[3]) and re_email.match(col[4]) \
                and re_pin.match(col[6]):
            bad_rows.append(row)
        else:
            # The row format is valid.
            #
            type        = col[0]
            id_hrns     = col[1]
            primid_hrns = col[2]
            currency    = col[3]
            email       = col[4]
            password    = col[5]
            pin         = col[6]

            if type == "primid":
                if primid_exists(id_hrns):
                    report_line = "primid\t" + id_fph + " exists already"
                    report.append(report_line)
                    break
                currency_fph = hrns_to_fph(currency)
                if not currency_exists(currency_fph):
                    bad_rows.append(row)
                    problems.append("Currency " + currency + " not found")
                    break

                primid_split = id_hrns.split(".")
                username = primid_split[0]
                namespace_hrns = ".".join(primid_split[1:])
                primid_fph = primid_create(
                                username,
                                namespace_hrns,
                                currency_fph,
                                password,
                                pin,
                                email,
                                ""
                             )
                report_line = "primid\t" + primid_fph + "\t" + id_hrns
                report.append(report_line)
            else: # type == "secid":
                if secid_exists(id_hrns):
                    report_line = "secid\t" + id_fph + " exists already"
                    report.append(report_line)
                    break
                if not primid_hrns:
                    report_line = "secid\t" + id_fph + " : primid not given"
                    report.append(report_line)
                    break
                secid_create(id_hrns, hrns_to_fph(primid_hrns))



# Values can only be imported into an empty set of accounts the the identity to
# which each belongs having been created already.

def import_account_values():

    return
