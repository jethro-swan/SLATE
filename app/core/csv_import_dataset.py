

from app.core.slate_core import identify_entity
from app.core.slate_core import complete_parent_namespace
from app.core.slate_core import new_currency
from app.core.slate_core import retrieve_pmap
from app.core.slate_core import new_pairing
from app.core.slate_core import split_hrns
from app.core.payments import ah_payment
from app.core.fph_hrns_maps import fph_to_hrns
from app.core.constants import NSS # NamseSpace Separator character

#==============================================================================
# CSV import
#
# This is a little different from the CSV import system used for
# *account*-to-*account* payments.
# (1) It works only with the UTF-8 Latin character set
# (2) It supports the automatic completion of incomplete namespace chains
# (3) It allows for the import of mixed entity types using a single CSV file
#
# The input format is:
#
#   | *currency* | payer *ahid* | payee *ahid* | amount | annotation |
#   | HRNS       | HRNS         | HRNS         |        |            |
#

def import_csv_dataset(fpath, primid_id):

    # The uploaded file will have been given a randomly generated name and is
    # identified as fpath. The file will be deleted as soon as it has been
    # fully processed.
    #
    # The separator-characted (SC) may be a comma, colon, semicolon or tab, but
    # the default is a comma.
    #
    # If any *currency* specified does not exist it will be created with the
    # uploading agent as its initial steward.
    #
    # If any *ahid* does not exist, it will be created and assigned to the
    # uploading agent.
    #
    # If any ancestor *namespace* does not exist it will be created with the
    # uploading agent as its initial steward.
    #
    # Any identifier imported here will be prefixed to the *primid* HRNS (i.e.
    # located within that *primid*'s private namesapce) unless prefixed with an
    # "@" character.

    errors = [] # a list of errors returned

    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if not primid_fph:
        errors.append(primid_id + " is not a registered identifier")
        return [], errors
    if not ("primid" in etypes):
        errors.append(primid_hrns + " has not registered primid")
        return [], errors

    report = ["New entities created:"] # a report of new entities created

    with open(fpath, "r") as csv_f:
        rows = csv_f.readlines()

    # Identify separator character from first row of the CSV file:
    #tries_left = 4
    tries = 0
    row0 = rows[0].strip()
    for c in [",", ":", ";", "\t"]:
        field = row0.split(c)
        if len(field) == 5:
            SC = c
            break

    row_count = 0
    for row in rows:
        row_count += 1
        field = row.split(SC)
        if len(field) != 5:
            errors.append("Row " + str(row_count) + ": Wrong number of fields")
            return report, errors
        currency_hrns_ = field[0].strip("\"")
        payer_ahid_hrns = field[1].strip("\"") + NSS + primid_hrns
        payee_ahid_hrns = field[2].strip("\"") + NSS + primid_hrns
        amount = int(100*float(field[3].strip("\"")))
        annotation = field[4].strip()

        if currency_hrns_[0] == "@": # absolute identifier path
            currency_hrns_ = currency_hrns_.lstrip("@")
        else: # relative identifier path
            currency_hrns_ = currency_hrns_ + NSS + primid_hrns

        # Create any missing *currency*:
        currency_fph, currency_hrns, etypes, \
        m = identify_entity(currency_hrns_)
        if not (currency_fph and ("currency" in etypes)):
            currency_name, parent_hrns = split_hrns(currency_hrns_)
            currency_fph, currency_hrns, \
            m = new_currency(
                    currency_name,
                    complete_parent_namespace(parent_hrns, primid_fph),
                    primid_fph,
                    "",
                    "",
                    currency_name # is used for default *account* name
                )
            if not currency_fph: # *currency* could not be created
                errors.append(
                    "Currency " + currency_hrns_ + " could not be created.\n" \
                    + m
                )
                continue
        pmap, m = retrieve_pmap(primid_fph)

        # Create any missing payer *ahid* and *ahid*|*currency* pairings.
        payer_ahid_name, parent_hrns = split_hrns(payer_ahid_hrns)
        parent_fph = complete_parent_namespace(parent_hrns, primid_fph)
        payer_account_fph, payer_account_hrns, \
        m = new_pairing(
                primid_hrns,
                payer_ahid_hrns,
                 currency_hrns
            )
        if payer_account_fph:
            report.append(payer_ahid_hrns + " created")
            report.append(fph_to_hrns(payer_account_fph) + " created")

        pmap, m = retrieve_pmap(primid_fph)

        # Create any missing payee *ahid* and *ahid*-*currency* pairings.
        payee_ahid_name, parent_hrns = split_hrns(payee_ahid_hrns)
        parent_fph = complete_parent_namespace(parent_hrns, primid_fph)
        payee_account_fph, payee_account_hrns, \
        m = new_pairing(
                primid_fph,
                payee_ahid_hrns,
                currency_hrns
            )
        if payee_account_fph:
            report.append(payee_ahid_hrns + " created")
            report.append(fph_to_hrns(payee_account_fph) + " created")

        pmap, m = retrieve_pmap(primid_fph)

        m = ah_payment(
                payer_ahid_hrns,
                payee_ahid_hrns,
                currency_hrns,
                amount,
                annotation
            )
        if m:
            errors.append(m)

    return report, errors

#==============================================================================
