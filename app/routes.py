import os
import json
from pathlib import Path
import sys
import pickle
import sqlite3

import bcrypt
from itsdangerous import URLSafeTimedSerializer

from datetime import datetime, date


## SLATE components: -----------------------------------------------------------

from app.core.constants import NSS
from app.core.constants import PAYMENTS_DB
from app.core.constants import SLATE_TEMP, IMPORT_QUEUE, IMPORTING

#from app.core.constants import SLATE_EXPORT, SLATE_IMPORT

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.fph_hrns_maps import hrns_exists_already

from app.core.common import unixtime_int

from app.core.slate_core import get_entity_type, get_account_currency
from app.core.slate_core import identify_entity, get_primid
from app.core.slate_core import new_primid, new_secid
from app.core.slate_core import update_primid_access_details
from app.core.slate_core import new_namespace, new_currency
from app.core.slate_core import new_account
from app.core.slate_core import account_status
from app.core.slate_core import list_stewardships, list_stewards
from app.core.slate_core import retrieve_primid_access_details
from app.core.slate_core import list_agent_accounts, list_secids
from app.core.slate_core import get_namespace_specific_properties
from app.core.slate_core import get_currency_specific_properties
from app.core.slate_core import get_account_specific_properties
from app.core.slate_core import set_default_currency
from app.core.slate_core import get_default_currency
from app.core.slate_core import list_all_namespaces
from app.core.slate_core import hrns_to_name_and_namespace
from app.core.slate_core import authenticate_primid_email
from app.core.slate_core import get_hub_mode
from app.core.slate_core import get_version
from app.core.slate_core import add_stewardship, remove_steward
from app.core.slate_core import random_filename

from app.core.omtrad import retrieve_pmap
from app.core.omtrad import create_new_pairing
#from app.core.omtrad import get_ahid_primid
from app.core.omtrad import retrieve_pairing_account_fph
from app.core.omtrad import ah_payment
from app.core.omtrad import import_csv_dataset
from app.core.omtrad import is_ancestor, is_in_private_namespace
from app.core.omtrad import get_ahid_primid

from app.core.slate_session import create_slate_session_db
from app.core.slate_session import session_save_currencies_available
from app.core.slate_session import session_retrieve_currencies_available
#from app.core.slate_session import retrieve_currency_options
from app.core.slate_session import session_save_payment_options
from app.core.slate_session import session_retrieve_payment_options
#from app.core.slate_session import session_save_payee_accounts_available
#from app.core.slate_session import session_retrieve_payee_accounts_available
from app.core.slate_session import remove_slate_session_data

from app.core.regexp_list import re_fph, re_hrns, re_email
from app.core.regexp_list import re_pvalue

from app.core.slate_login import get_auth_data, register_authenticated_login

##from app.core.auth import pin_random_ord, pin_prompt_message
from app.core.auth import pin_subset_prompt
from app.core.auth import check_auth_hash, authenticate_pin

from app.core.logging import log_event

from app.core.payments import payment

from app.core.exports import list_payments_for_account
from app.core.exports import dump_account_payments_csv
from app.core.exports import list_payments_in_currency
from app.core.exports import dump_currency_payments_csv

from app.core.uploads import csv_create_namespaces
from app.core.uploads import csv_create_identities
from app.core.uploads import csv_create_currencies
from app.core.uploads import csv_create_accounts

#from app.core.messaging import display_colour_subject_prefix
#from app.core.messaging import category_display_colour
from app.core.messaging import create_messages_db
from app.core.messaging import send_message
from app.core.messaging import fetch_messages
from app.core.messaging import messages_available
from app.core.messaging import delete_message

from app.core.mail_temp import temp_mail_send

from app.core.display import yesno, integer_to_money_format
from app.core.display import etype_to_adtype

from app.core.csv_import import import_minimal_payment_set_as_csv

#from app.site_configuration import site_config

#from app import bcrypt # added 2024-11-10

#, authenticate_web_access
#from app.core.auth import set_web_password_hash


# Flask components: -----------------------------------------------------------

from flask import render_template, render_template_string
from flask import flash, redirect, url_for
from flask import session, g, request
#from flask_mailman import Mail, EmailMessage
#from flask_mailman import EmailMessage
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_login import login_required
from flask import send_file
#from flask import send_from_directory
from app import app

#from app import mail # from __init__.py

from app.models import User

from app.forms import LoginForm, RegistrationForm
from app.forms import LoginRecoveryForm, LoginResetForm
from app.forms import PaymentToAccountForm
from app.forms import PaymentToIdentityForm
from app.forms import PaymentAccountPairForm
from app.forms import CurrencyCreateForm
from app.forms import AccountCreateForm
from app.forms import AccountCreateFormMinimal
from app.forms import NamespaceCreateForm
from app.forms import SecidCreateForm
from app.forms import SpecifyPayeeAccountForm
from app.forms import SpecifyPayeeAgentForm
from app.forms import SelectPayerAndPayeeAccountsForm
from app.forms import SpecifyPayeeAccountHolderForm
from app.forms import SpecifyPayeeAgentAndCurrencyForm
from app.forms import PayeeCurrencyAmountPaymentForm
from app.forms import StewardAddForm
from app.forms import UserMessageForm
#from app.forms import TQueueForm
from app.forms import FileUploadForm
from app.forms import PairingCreateForm
from app.forms import CSVImportForm

from markupsafe import escape

#------------------------------------------------------------------------------




#------------------------------------------------------------------------------
# Shared local functions:

# Create the identity type display string:
def fph_to_display_type(agent_identifier):
    agent_fph, \
    agent_hrns, \
    etype, \
    m = identify_entity(agent_identifier)
    if etype == "primid":
        return "login identity"
    elif etype == "secid":
        return "alias"
    else:
        return ""

# The *primid* need be displayed only if the current active *identity* is a
# *secid*:
def fph_to_primid_iff_needed(agent_identifier):
    agent_fph, \
    agent_hrns, \
    etype, \
    m = identify_entity(agent_identifier)
    etype, m = get_entity_type(agent_fph)
    if etype == "secid":
        primid_fph = get_primid(agent_fph)
        primid_hrns = fph_to_hrns(primid_fph)
        return primid_fph, primid_hrns
    else:
        return "", ""

#------------------------------------------------------------------------------

development_mode = False


# registration ----------------------------------------------------------------
@app.route("/register", methods = ["GET", "POST"])
def register():
    #page = "register"
    # In a typical situation where the new user is invited (via QR-coded link)
    # to register, it is likely that both the currency and a geographically
    # appropriate user namespace will be specified. However, that will not
    # necessarily always be the case. Since neither, either or both may be
    # provided in the invitation link, the request.args variable is used
    # instead so the route may look like any of the following:
    #   /register
    #   /register?c_fph = 0c75584102039b93
    #   /register?c_fph = 0c75584102039b93&ns_fph = 95a5467fed65bbac
    #   /register?ns_fph = 95a5467fed65bbac

    # The following variables are used to determine which menu subsets are
    # displayed:
    page = "registration"
    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    # This one may not be needed:
    mode = "logged_out"

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    #--------------------------------------------------------------------------
    # The following seven variables determine which of the registration form's
    # fields are displayed:
    address_details_included = False
    location_details_included = False
    phone_details_included = False
    recovery_questions_included = False
    notification_option_included = False
    country_included = False
    ssh_public_key_allowed = False
    #--------------------------------------------------------------------------

    url_currency_identifier = request.args.get("c_fph")
    initial_currency_fph, \
    initial_currency_hrns, \
    etype, \
    m = identify_entity(url_currency_identifier)
    if m:
        flash(m)
        return redirect("/register")
    if not (initial_currency_fph and (etype == "currency")):
        initial_currency_fph = ""
        initial_currency_hrns = ""

#    print("currency: " + initial_currency_fph + " > " + initial_currency_hrns)

    initial_namespace_identifier = request.args.get("s_fph")
    initial_namespace_fph, \
    initial_namespace_hrns, \
    etype, \
    m = identify_entity(initial_namespace_identifier)
    #if m:
    #    flash(m)
    #    return redirect("/register")
    if not (initial_namespace_fph and (etype == "namespace")):
        initial_namespace_fph = ""
        initial_namespace_hrns = ""

    form = RegistrationForm()

    # The fields displayed depend upon the policy set by the stewards of the
    # initial *currency* and *namespace&. For example, for some *currencies*
    # (many perhaps) it may be considered very useful to have some information
    # about the geographical location of the user's base (home or business
    # address), particularly where this is going to be used to create a map
    # overlay.

    if form.validate_on_submit():

        username = form.username.data

        if hub_mode == "slate_minimal":
            namespace_identifier, m = hrns_to_fph("cc")
        else:
            namespace_identifier = form.namespace.data.strip().lstrip(".")

        if hub_mode == "slate_minimal":
            currency_identifier, m = hrns_to_fph("cc")
##            currency_identifier, m = hrns_to_fph("hrs.cc")
        else:
            currency_identifier = form.currency.data.strip()

        if form.realname.data is not None:
            real_name = form.realname.data
        else:
            real_name = ""

        email1 = form.email_1.data          # required
        if form.email_2.data is not None:
            email2 = form.email_2.data      # optional
        else:
            email2 = ""

        password = form.password.data
        pin = form.pin.data

        # At this point the initial *currency* may have been specified in
        # either the URL or the form. If the *currency* FPH was specified in
        # the URL, the *currency* HRNS field will not have been displayed.

#        if hub_mode == "slate_minimal":
#            currency_identifier, m = hrns_to_fph("hrs.cc")
#        else:
#            currency_identifier = form.currency.data.strip()  # (from the form)
        # The identify_entity( ) function determines whether either is valid.
        currency_fph, \
        currency_hrns, \
        etype, \
        m = identify_entity(currency_identifier)
        if m:
            log_event("error", "currency", m)
            flash("Unknown error (logged)")
            return redirect("/register")
        if not currency_fph:
            flash("No valid currency identifier provided")
            return redirect("/register")
        if etype !=  "currency":
            flash(currency_identifier + " is not a currency")
            return redirect("/register")

        # Similarly, at this point the parent *namespace* may have been
        # specified in either the URL or the form. If the parent *namespace*
        # FPH was specified in the URL, the *currency* HRNS field will not have
        # been displayed.

#        namespace_identifier = form.namespace.data

#        if hub_mode == "slate_minimal":
#            namespace_fph, m = hrns_to_fph("cc")
#        else:
#            namespace_identifier = form.namespace.data.strip().lstrip(".")
        # The identify_entity( ) function determines whether either is valid.
        namespace_fph, \
        namespace_hrns, \
        etype, \
        m = identify_entity(namespace_identifier)
        if m:
            log_event("error", "namespace", m)
            flash("Unknown error (logged)")
            return redirect("/register")
        if not namespace_fph:
            flash("The namespace specified does not exist")
            return redirect("/register")

# 2025-04-08:   Changed to accommodate use of any entity identifier as a
#               *namespace* identifier, e.g.
#               cc  as both seed *namespace* and seed *currency*
        if etype == "account":
            flash(namespace_identifier + ": invalid parent namespace")
            return redirect("/register")

#        if etype != "namespace":
#            flash(namespace_identifier + " is not a namespace")
#            return redirect("/register")
        # If control reaches this point then *namespace* (whether specified
        # in the form or in the URL) exists.




        if form.password_repeat.data != form.password.data:
            flash("The passwords not not match")
            return redirect("/register")

#        print("form.username.data = " + username)
#        print("namespace_fph      = " + namespace_fph)
#        print("form.realname.data = " + real_name)
#        print("form.email_1.data  = " + email1)
#        print("form.password.data = " + password)
#        print("form.pin.data      = " + pin)


        primid_fph, \
        primid_hrns, \
        access_token, \
        m = new_primid(
                form.username.data,
                namespace_fph,
                form.realname.data,
                form.email_1.data,
                form.email_2.data,
                form.password.data,
                form.pin.data
            )
        if m:
            log_event("error", "primid creation", m)
            flash(m)
            return redirect("/register")

        # An initial *account* will now be created (in the new *primid*'s
        # private *namespace*) using the default name associated with the
        # specified *currency*.

        currency_fph, \
        currency_hrns, \
        prefix, \
        suffix, \
        default_account_name, \
        stewards_list, \
        m = get_currency_specific_properties(currency_fph)
        if m:
            flash(m)
            return redirect("/register")
        if currency_fph == "":
            flash("The currency specified does not exist.")
            return redirect("/register")

        account_fph, \
        account_hrns, \
        m = new_account(
                default_account_name,
                primid_fph,
                primid_fph,
                "", # *ahid_fph* not required here
                currency_fph
            )
        if m:
            log_event("error", "account creation", m)
            flash("The account cannot be created. See error log.")
            return redirect("/register")

        flash(primid_hrns + " has been registered")
        flash(account_hrns + " has been created in currency " + currency_hrns)
        return redirect("/")

    # If control has reached this point then the new *primid* has been created.
    # Its SSH CLI access token has been recorded already and will be visible to
    # the *primid*'s owner when logged in.
    #
    # Now we need to create an initial *account* for this new *primid*. This
    # will be given the name of the specified *currency* and anchored in the
    # *primid*'s private *namespace*, i.e.
    #
    return render_template(
        "register.html",
        title = "User registration",
        form = form,
        logged_in = logged_in,
        page = page,
        mode = mode,
        hub_mode = hub_mode,
        version = get_version(),
        development_mode = development_mode,
        initial_namespace_fph = initial_namespace_fph,
        initial_namespace_hrns = initial_namespace_hrns,
        initial_currency_fph = initial_currency_fph,
        initial_currency_hrns = initial_currency_hrns,
        namespace_steward = False,
        currency_steward = False
    )

# login -----------------------------------------------------------------------
@app.route("/", methods = ["GET", "POST"])
@app.route("/login", methods = ["GET", "POST"])
def login():
    page = "login" # Variable used to identify which menu items to display.
    mode = "logged_out"
    logged_in = False
    if current_user.is_authenticated: # user is already logged in
        mode = "logged_in"
        logged_in = True
        return redirect(url_for("home"))

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    form = LoginForm()
    if form.validate_on_submit():

        agent_identifier = form.identity.data # HRNS or FPH

        if (agent_identifier == "") and (email == ""): # neither provided
            flash("Either an identity or an email address must be provided")
            return redirect(url_for("login"))

        primid_has_been_identified_from_identity = False
        primid_has_been_identified_from_email = False

        if agent_identifier:
            identity_fph, \
            identity_hrns, \
            etype, \
            m = identify_entity(form.identity.data)
            if m:
                flash(m)
                return redirect(url_for("login"))
            if (etype !=  "primid") and (etype !=  "secid"):
                flash("Invalid identity entered")
                return redirect(url_for("login"))
            if etype == "secid": # authentication requires primary *identity*
                primary_identity_fph, m = get_primid(identity_fph)
                if m:
                    flash(m)
                    log_event(
                        "errors", "primid entification",
                        "The primid cannot be identified from " + identity_fph
                    )
                    return redirect(url_for("login"))
            if etype == "primid":
                primary_identity_fph = identity_fph
            if primary_identity_fph:
                # If control reaches this point and the FPH exists, we have a
                # valid *primid* for the HRNS or FPH entered.
                primid_has_been_identified_from_identity = True
            else:
                flash(identity_fph + " is not a registered identity.")
        else:
            flash("No valid identifier has been provided.")
            return redirect(url_for("login"))

        password_hash, \
        stored_pin, \
        access_token_hash, \
        m = get_auth_data(primary_identity_fph)
        if m:
            flash(m)
            return redirect(url_for("login"))

        # Retrieve the user object:
        user = User(primary_identity_fph)

        password = form.password.data
        password2 = form.password.data.strip()
#        if password !=  password2:
#            print("password corrupted")

        pwd = password
        pwd_hash = password_hash
        if not bcrypt.checkpw(pwd.encode("utf-8"), pwd_hash.encode("utf-8")):
            return redirect(url_for("login"))

        if not authenticate_pin(stored_pin, form.pse.data, form.pro.data):
            flash("Incorrect PIN digits")
            return redirect(url_for("login"))

        # Register the authenticated login:
        register_authenticated_login(primary_identity_fph)

        login_user(user, remember = form.remember_me.data)

        session["login_identity"] = identity_fph    # Initial values upon login
        session["working_identity"] = identity_fph  #

        if hub_mode == "omtrad":

            session["previous_page"] = "home_ahc"   # (This one subsequently
                                                    # serves as shift register).
            return redirect(url_for("home_ahc"))

        else:

            session["previous_page"] = "home"       # (This one subsequently
                                                    # serves as shift register).
            return redirect(url_for("home"))


    return render_template(
        "login.html",
        title = "Sign in",
        page = page,
        mode = mode,           # ???
        hub_mode = hub_mode,
        version = get_version(),
        logged_in = logged_in, # ???
        form = form,
        development_mode = development_mode
    )

# log out ---------------------------------------------------------------------
@app.route("/logout")
@login_required
def logout():

    user = current_user.get_id()
#    print("current_user.get_id() = " + user + " = " + fph_to_hrns(user))
#    deregistered, m = current_user.mark_unauthenticated()
#    if deregistered:
#        logout_user() # a Flask function
#        return redirect(url_for("login"))
#    else:
#        if m:
#            flash(m)
#        flash("Unable to log out (see error log)")
#        log_event("errors", "logout problem", user + " unable to log out")
#        return redirect(url_for("home"))

    logout_user() # a Flask function
    return redirect(url_for("login"))



# login recovery request ------------------------------------------------------
@app.route("/login/recover", methods = ["GET", "POST"])
def login_recover():
    if current_user.is_authenticated: # should be false
        return redirect(url_for("login"))

    page = "login_recovery"
    mode = "logged_out"

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()

    form = LoginRecoveryForm()
    if form.validate_on_submit():
        agent_identifier = form.identity.data
        agent_email = form.email.data

        agent_fph, \
        agent_hrns, \
        agent_type, \
        m = identify_entity(agent_identifier)

        if agent_type == "secid":
            agent_primid_fph = get_primid(agent_fph)
        elif agent_type == "primid":
            agent_primid_fph = agent_fph
        else:
            flash(agent_identifier + " is not a registered identity")
            return redirect(url_for("login"))

        # If control reaches this point, the entity identifier entered has been
        # confirmed to be or have a registered *primid*.

        # An valid email address is required in order to send a recovery link:
        if not agent_email:
            flash("Login recovery is not possible without an email address.")
            return redirect(url_for("login"))

        if not authenticate_primid_email(agent_primid_fph, agent_email):
            flash(
                "The email is address " + agent_email + " is not registered " \
                + "for user " + agent_identifier
            )
            return redirect(url_for("login"))

        # If control reaches this point, we have a valid email address for the
        # identity entered.

        password_hash, \
        stored_pin, \
        access_token_hash, \
        m = get_auth_data(agent_primid_fph)

#        token_salt = password_hash  # Used to invalidate the login reset token
                                    # once the password has been changed. [1]
#        reset_token_data = {
#                               "agent_primid_fph" : agent_primid_fph,
#                               "agent_email" : agent_email
#                           }
        reset_token_data = agent_primid_fph
        serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
        login_reset_token = serializer.dumps(
                                           agent_primid_fph,
                                           salt = password_hash
                                       )
        login_reset_url = url_for(
                              "login_reset",
                              user_id = agent_primid_fph,
                              token = login_reset_token,
                              _external = True
                          )
#        login_reset_url = url_for("login_reset") \
#                        + "/" + agent_primid_fph + "/" + login_reset_token

#        print(login_reset_token)
#        print(login_reset_url)

        message_body = "You have received this message because a login " \
                     + " recovery link has been requested.\n" \
                     + "\nTo reset your password and PIN, click on:\n" \
                     + login_reset_url + " (or copy and paste it into your " \
                     + "browser's address bar.\n\n" \
                     + "\nIf you have not requested a login recovery " \
                     + "link, you can ignore this message.\n\n"

        temp_mail_send(
            "server@lrc.org.uk",
            agent_email,
            "Reset your password and PIN",
            message_body
        )

        flash(
            "Password/PIN reset instructions have been sent to " + agent_email
        )

        return redirect("/login")

    return render_template(
        "login_recovery.html",
        title = "Login recovery",
        form = form,
        page = page,
        mode = mode,
        hub_mode = hub_mode,
        version = get_version()
    )

# [1] Thanks to https://freelancefootprints.substack.com/p/
#     yet-another-password-reset-tutorial
#     for this and many other useful hints and suggestions.)

# ==============================================================================
# login reset
@app.route("/login/reset/<user_id>/<token>", methods = ["GET", "POST"])
def login_reset(user_id, token):
    if current_user.is_authenticated: # should be false
        return redirect(url_for("login"))

    page = "login_reset"
    mode = "logged_out"

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(user_id) # from URL slug

    password_hash, \
    stored_pin, \
    access_token_hash, \
    m = get_auth_data(user_id) # from URL slug

#    print(
#        "SECRET_KEY = " \
#        + app.config["SECRET_KEY"]
#    )
#    print(
#        "RESET_PASS_TOKEN_MAX_AGE = " \
#        + str(app.config["RESET_PASS_TOKEN_MAX_AGE"])
#    )

    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    reset_token_data = serializer.loads(
                            token,
                            #max_age = 900,
                            #max_age = app.config["RESET_PASS_TOKEN_MAX_AGE"],
                            salt = password_hash
                        )
#    print(type(reset_token_data))
#    print(reset_token_data)

#    if reset_token_data["agent_primid_fph"] !=  identity_fph:
    if reset_token_data !=  primary_identity_fph:
        flash("Login reset token error")
        return redirect("/login")

#    print("user_id = " + user_id + " > " + fph_to_hrns(user_id))

    form = LoginResetForm()
    if form.validate_on_submit():
        flash("Registration submitted for user " + fph_to_hrns(user_id))
        if form.password_repeat.data !=  form.password.data:
            flash("The passwords not not match")
            return redirect("/login")

        m = update_primid_access_details(
                primary_identity_fph,
                form.password.data,
                form.pin.data
            )
        if m:
            flash(m)
            flash("Unable to reset login credentials")
            return redirect("/login")
        else:
            flash("Password/PIN reset successful.")
            return redirect("/login")

    return render_template(
        "login_reset.html",
        title = "User login reset",
        primary_identity_hrns = primary_identity_hrns,
        form = form,
        hub_mode = hub_mode,
        version = get_version()
    )

# ==============================================================================
# change working identity
##@app.route("/change_working_identity/<new_identity_fph>",
@app.route("/identity/change/<new_identity_fph>",
           methods = ["GET", "POST"])
@login_required
def change_working_identity(new_identity_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()

    #version = get_version()()


    new_identity_fph, \
    new_identity_hrns, \
    new_identity_type, \
    m = identify_entity(new_identity_fph)
    if m:
        flash(m)
        return redirect("/home")
    if new_identity_fph == "":
        flash(new_identity_fph + " is not a valid identity")
        return redirect("/home")

    login_identity_fph, \
    login_identity_hrns, \
    login_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        current_working_identity_fph = session["working_identity"]
    else:
        session["working_identity"] = login_identity_fph
        current_working_identity_fph = login_identity_fph

    current_identity_fph, \
    current_identity_hrns, \
    current_identity_type, \
    m = identify_entity(current_working_identity_fph)

    if new_identity_fph == current_identity_fph:
        flash("No change of identity has been requested")
        return redirect("/home")

    identities_fph_list = list_secids(login_identity_fph)
    identities_fph_list.append(login_identity_fph)
    if new_identity_fph in identities_fph_list:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(new_identity_fph)
        session["working_identity"] = working_identity_fph
        flash("Working identity changed to " + working_identity_hrns)
        return redirect("/home")
    else:
        working_identity_fph = current_identity_fph
        working_identity_hrns = current_identity_hrns
        working_identity_type = current_identity_type
        return redirect("/home")

#==============================================================================
# login landing page

@app.route("/home/new", methods = ["GET", "POST"])
@login_required
def new_home():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "new_home"
    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
#        session["previous_page"] = "home" ### probably not needed
        previous_page = "home"
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    hub_mode = get_hub_mode()
    #version = get_version()()
 ### New variable added

    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    ## SOME OF THE FOLLOWING WILL NOT BE NEEDED

    # The user logs in as the *primid*, even if indirectly as one of its
    # *secid*s, but once logged in will see all of its *identities* along with
    # a list of *accounts* belonging to each. The user will also see a list of
    # entities over which it holds/shares stewardship.

    stewardships_list, m = list_stewardships(primary_identity_fph)

    # Since a user may have *accounts* scattered across an arbitrary number of
    # *namespaces*, it is necessary to maintain a list of these:

    # A full list of *identities* is compiled, with the *primid* first:
    identities_list = list_secids(primary_identity_fph)
    identities_list.insert(0, primary_identity_fph)

    identities = [] # list of *identity* dictionaries) to "home.html" template.

    lid_messages = fetch_messages(primary_identity_fph)   # Always display
    wid_messages = fetch_messages(working_identity_fph)



#
    return render_template(
            "new_home.html",
            title = "Home",
            page = page,
            group = group,
            hub_mode = hub_mode,
            version = get_version(),
            logged_in = logged_in,
            primary_identity_type = "login identity",
            primary_identity_fph = primary_identity_fph,
            primary_identity_hrns = primary_identity_hrns,
            working_identity_fph = working_identity_fph,
            working_identity_hrns = working_identity_hrns,
            working_identity_type = working_identity_type,

            lid_messages = lid_messages,
            wid_messages = wid_messages

            # List of (nested) dictionaries for display in "home.html":
#            identities = identities,
#            secids = secids,
#            stewardships = stewardships
        )

@app.route("/hold")
@login_required
def hold():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    if hub_mode != "omtrad":
        flash("Operational mode invalid for this endpoint")
        return redirect("/home")

    page = "hold"
    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
        previous_page = "home_ahc"
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    # In omtrad mode, the working *identity* is always the *primid*.
    working_identity_fph = primary_identity_fph
    working_identity_hrns = primary_identity_hrns
    working_identity_type = primary_identity_type

    return render_template(
        "hold.html",
        title = "Hold",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        logged_in = logged_in,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
    )




@app.route("/home_ahc", methods=["GET", "POST"])
@login_required
def home_ahc():

    # If a dataset import if in progress, do not allow any FPH>HRNS or
    # HRNS>FPH mapping operations to be initiated by a browser refresh.
    # Instead, display a holding page.
    if os.path.exists(IMPORTING):
        return redirect("/hold")

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    if hub_mode != "omtrad":
        flash("Operational mode invalid for this endpoint")
        return redirect("/home")

    page = "home_ahc"
    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
        previous_page = "home_ahc"
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    # In omtrad mode, the working *identity* is always the *primid*.
    working_identity_fph = primary_identity_fph
    working_identity_hrns = primary_identity_hrns
    working_identity_type = primary_identity_type

    stewardships_list, m = list_stewardships(primary_identity_fph)

    pmap_t, m = retrieve_pmap(primary_identity_fph)

    p_rows = []

    for ahid_hrns in pmap_t.keys():
#        print(ahid_hrns)
        for currency_hrns in pmap_t[ahid_hrns].keys():

#            print(" "*4 + currency_hrns)

            account_fph = pmap_t[ahid_hrns][currency_hrns]
#            print(" "*8 + account_fph)

            account_exists, \
            account_active, \
            account_currency_fph, \
            account_owner_fph, \
            account_ahid_fph, \
            account_balance, \
            account_volume, \
            m = account_status(account_fph)

            if fph_to_hrns(account_currency_fph) != currency_hrns:
                continue # (This should never happen)

            currency_fph, \
            currency_hrns, \
            prefix, \
            suffix, \
            default_account_name, \
            stewards_list, \
            m = get_currency_specific_properties(account_currency_fph)

            p_row = {}
            p_row["currency_hrns"] = currency_hrns
            p_row["ahid_hrns"] = ahid_hrns
            p_row["ahid_fph"], m = hrns_to_fph(ahid_hrns)
            p_row["account_fph"] = account_fph
            p_row["account_owner_fph"] = account_owner_fph
            p_row["account_owner_hrns"] = fph_to_hrns(account_owner_fph)
            p_row["balance"] = integer_to_money_format(account_balance)
            p_row["isneg"] = (account_balance < 0)
            p_row["prefix"] = prefix
            p_row["suffix"] = suffix
            p_row["volume"] = integer_to_money_format(account_volume)
            if currency_fph in stewardships_list:
                p_row["primid_currency_steward"] = True
            else:
                p_row["primid_currency_steward"] = False
            p_row["currency_fph"] = currency_fph
            p_rows.append(p_row)


    # Sorting by *currency* and *ahid* (quick and dirty method)

    currencies_list = []
    for row in p_rows:
        currency = row["currency_hrns"]
        if not(currency in currencies_list):
            currencies_list.append(currency)
    currencies_list.sort()
#    print(currencies_list)

    ahid_lists_dict = {}
    for currency in currencies_list:
        ahid_lists_dict[currency] = []
        for row in p_rows:
            ahid = row["ahid_hrns"]
            if not(ahid in ahid_lists_dict[currency]):
                ahid_lists_dict[currency].append(ahid)
        ahid_lists_dict[currency].sort()
#    print(ahid_lists_dict)

    p_rows2 = []
    for currency in currencies_list:
        for ahid in ahid_lists_dict[currency]:
#            print(currency + " : " + ahid)
            for row in p_rows:
                if (row["currency_hrns"] == currency) and \
                   (row["ahid_hrns"] == ahid):
                    p_rows2.append(row)

#    for row in p_rows2:
#        print(row)






#    # TEST STUFF
#    print()
#    print(pmap_t)
#    print()
#    print("="*80)
#    for ahid_hrns in pmap_t.keys():
#        print(ahid_hrns)
#        for currency_hrns in pmap_t[ahid_hrns].keys():
#            print(" "*4 + currency_hrns)
#            for ap in pmap_t[ahid_hrns][currency_hrns].keys():
#                if ap:
#                    print(" "*8 + "{0: <30}".format(ap) + " :: ", end="")
#                    print(pmap_t[ahid_hrns][currency_hrns][ap])
#    print("="*80)
#    print()
#
#
#    for p_row in p_rows:
#        print(p_row)






    return render_template(
        "home_ahc.html",
        title = "Home",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        development_mode = development_mode,
        logged_in = logged_in,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        p_rows = p_rows2,
        pmap_t = pmap_t
    )


## NB: This will be assigned a new endpoint to allow "/home" to be used for a
##     sparser login landing page centred around internal messaging.

@app.route("/home/full", methods = ["GET", "POST"])
@app.route("/home", methods = ["GET", "POST"])
@login_required
def home():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    if hub_mode == "omtrad":
        return redirect("/home_ahc")

    page = "home"
    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    elif hub_mode == "omtrad":
        previous_page = "home_ahc"
        return redirect("/home_ahc")
    else:
        previous_page = "home"
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)


    # List all identities:
    identity_list = []
    identity_list.append(primary_identity_fph)
    secids_list = list_secids(primary_identity_fph)
    for secid_fph in secids_list:
        identity_list.append(secid_fph)

#    print("Indentities listed:")
#    for identity_fph in identity_list:
#        print("\t" + fph_to_hrns(identity_fph))

    total_number_of_messages = 0
    total_number_of_indelible_messages = 0
    # List identities for which messages are available:
    message_recipients_list = [] # (list of dictionaries for template)
    for identity_fph in identity_list:
        number_of_messages, \
        number_of_indelible_messages = messages_available(identity_fph)

#        print("number_of_messages = " + str(number_of_messages))
#        print(
#            "number_of_indelible_messages = " \
#            + str(number_of_indelible_messages)
#        )
        total_number_of_messages += number_of_messages
        total_number_of_indelible_messages += number_of_indelible_messages

    if total_number_of_messages > 0:
        number_of_messages = str(total_number_of_messages)
    else:
        number_of_messages = ""
    if total_number_of_indelible_messages > 0:
        number_of_indelible_messages = str(total_number_of_indelible_messages)
    else:
        number_of_indelible_messages = ""

#    number_of_wid_messages, d = messages_available(working_identity_fph)
#    number_of_messages = number_of_wid_messages + number_of_primid_messages
#    if number_of_messages > 0:
#        number_of_messages = str(number_of_messages)
#    else:
#        number_of_messages = ""

    # The user logs in as the *primid*, even if indirectly as one of its
    # *secid*s, but once logged in will see all of its *identities* along with
    # a list of *accounts* belonging to each. The user will also see a list of
    # entities over which it holds/shares stewardship.

    stewardships_list, m = list_stewardships(primary_identity_fph)

    # Since a user may have *accounts* scattered across an arbitrary number of
    # *namespaces*, it is necessary to maintain a list of these:

    # A full list of *identities* is compiled, with the *primid* first:
    identities_list = list_secids(primary_identity_fph)
    identities_list.insert(0, primary_identity_fph)

    identities = [] # list of *identity* dictionaries) to "home.html" template.

    for id_fph in identities_list:

        id = {} # the outer dictionary for this *identity*

        id_fph, \
        id_hrns, \
        etype, \
        m = identify_entity(id_fph)
        if m:
            flash(m)

        id["fph"] = id_fph
        id["hrns"] = fph_to_hrns(id_fph)
        if etype == "primid":
            id["type"] = "login identity"
        elif etype == "secid":
            id["type"] = "alias"
        else:
            etype == "poltergeist" # something to be investigated

        accounts_list, m = list_agent_accounts(id_fph)
        if m:
            flash(m)

        # List the *accounts* belonging to this *identity*:
        accounts = [] # (second-level dictionary for iteration in template)
        for account_fph in accounts_list:
            # Fetch account details:
            account_currency_fph, \
            account_owner_fph, \
            account_ahid_fph, \
            account_balance, \
            account_volume, \
            m = get_account_specific_properties(account_fph)

            # Fetch currency details:
            currency_fph, \
            currency_hrns, \
            prefix, \
            suffix, \
            default_account_name, \
            stewards_list, \
            m = get_currency_specific_properties(account_currency_fph)

            # Assemble a dictonary of *account* properties:
            a = {}
            a["fph"] = account_fph
            a["hrns"] = fph_to_hrns(account_fph)
            a["owner_fph"] = account_owner_fph
            a["owner_hrns"] = fph_to_hrns(account_owner_fph)
            a["balance"] = integer_to_money_format(account_balance)
            a["isneg"] = (account_balance < 0)
            a["prefix"] = prefix
            a["suffix"] = suffix
            a["volume"] = integer_to_money_format(account_volume)
            #primid_currency_steward = (currency_fph in stewardships_list)
            if currency_fph in stewardships_list:
                primid_currency_steward = True
            else:
                primid_currency_steward = False
            a["primid_is_currency_steward"] = primid_currency_steward
            a["currency_fph"] = currency_fph
            a["currency_hrns"] = currency_hrns
            accounts.append(a)

            # The following dictionary is used in template only if
            # HUB_MODE = "omtrad")




            # The following dictionary is used in template only if
            # HUB_MODE = "slate_simple")
            #account_hrns = fph_to_hrns(account_fph)
#            p["currency"] = {}
#            p["currency"]["fph"] = currency_fph
#            p["currency"]["hrns"] = currency_hrns
#            p["currency"]["identity"] = {}
#            p["currency"]["identity"]["account"] = {}
#            p["currency"]["identity"]["account"]["fph"] = account_fph
            #p["currency"]["identity"]["account"]["hrns"] = account_hrns
#            payment_option.append(p)
            # This is a temporary fudge.

        id["accounts"] = accounts
        identities.append(id)

    # If this is a *primid*, fetch a list of its *secid*s and stewardships:
    secid_list = list_secids(primary_identity_fph)
    secids = []
    for secid_fph in secid_list:
        secid = {}
        if secid_fph != "":
            secid["fph"] = secid_fph
            secid["hrns"] = fph_to_hrns(secid_fph)
            secids.append(secid)

    stewardships = []
    for stewardship_fph in stewardships_list:
        if stewardship_fph !=  "":
            stewardship = {}
            entity_fph, \
            entity_hrns, \
            etype, \
            m = identify_entity(stewardship_fph)
            stewardship["fph"] = stewardship_fph
            stewardship["hrns"] = entity_hrns
            stewardship["etype"] = etype
            stewardships.append(stewardship)

    return render_template(
        "home.html",
        title = "Home",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        development_mode = development_mode,
        logged_in = logged_in,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,

        # List of (nested) dictionaries for display in "home.html":
        identities = identities,
        secids = secids,
        stewardships = stewardships,
        number_of_indelible_messages = number_of_indelible_messages,
        number_of_messages = number_of_messages
    )




#==============================================================================
# This variant of the /home endpoint prioritizes *accounts* over *identities*
# and *currencies*.
#
@app.route("/list/accounts", methods = ["GET", "POST"])
@login_required
def list_accounts():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "list_accounts"
    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
        previous_page = "home"
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    # The user logs in as the *primid*, even if indirectly as one of its
    # *secid*s, but once logged in will see all of its *identities* along with
    # a list of *accounts* belonging to each. The user will also see a list of
    # entities over which it holds/shares stewardship.

    stewardships_list, m = list_stewardships(primary_identity_fph)

    # Since a user may have *accounts* scattered across an arbitrary number of
    # *namespaces*, it is necessary to maintain a list of these:

    # A full list of *identities* is compiled, with the *primid* first:
    identities_list = list_secids(primary_identity_fph)
    identities_list.insert(0, primary_identity_fph)

    identities = [] # list of *identity* dictionaries) to "home.html" template.

    for id_fph in identities_list:

        id = {} # the outer dictionary for this *identity*

        id_fph, \
        id_hrns, \
        etype, \
        m = identify_entity(id_fph)
        if m:
            flash(m)

        id["fph"] = id_fph
        id["hrns"] = fph_to_hrns(id_fph)
        if etype == "primid":
            id["type"] = "login identity"
        elif etype == "secid":
            id["type"] = "alias"
        else:
            etype == "poltergeist" # something to be investigated

        accounts_list, m = list_agent_accounts(id_fph)
        if m:
            flash(m)

        # List the *accounts* belonging to this *identity*:
        accounts = [] # (second-level dictionary for iteration in template)
        for account_fph in accounts_list:
            # Fetch account details:
            account_currency_fph, \
            account_owner_fph, \
            account_ahid_fph, \
            account_balance, \
            account_volume, \
            m = get_account_specific_properties(account_fph)

            # Fetch currency details:
            currency_fph, \
            currency_hrns, \
            prefix, \
            suffix, \
            default_account_name, \
            stewards_list, \
            m = get_currency_specific_properties(account_currency_fph)

            # Assemble a dictonary of *account* properties:
            a = {}
            a["fph"] = account_fph
            a["hrns"] = fph_to_hrns(account_fph)
            a["owner_fph"] = account_owner_fph
            a["owner_hrns"] = fph_to_hrns(account_owner_fph)
            a["balance"] = integer_to_money_format(account_balance)
            a["isneg"] = (account_balance < 0)
            a["prefix"] = prefix
            a["suffix"] = suffix
            a["volume"] = integer_to_money_format(account_volume)
            #primid_currency_steward = (currency_fph in stewardships_list)
            if currency_fph in stewardships_list:
                primid_currency_steward = True
            else:
                primid_currency_steward = False
            a["primid_is_currency_steward"] = primid_currency_steward
            a["currency_fph"] = currency_fph
            a["currency_hrns"] = currency_hrns
            accounts.append(a)

        id["accounts"] = accounts
        identities.append(id)

    # If this is a *primid*, fetch a list of its *secid*s and stewardships:
    secid_list = list_secids(primary_identity_fph)
    secids = []
    for secid_fph in secid_list:
        secid = {}
        if secid_fph != "":
            secid["fph"] = secid_fph
            secid["hrns"] = fph_to_hrns(secid_fph)
            secids.append(secid)

    stewardships = []
    for stewardship_fph in stewardships_list:
        if stewardship_fph !=  "":
            stewardship = {}
            entity_fph, \
            entity_hrns, \
            etype, \
            m = identify_entity(stewardship_fph)
            stewardship["fph"] = stewardship_fph
            stewardship["hrns"] = entity_hrns
            stewardship["etype"] = etype
            stewardships.append(stewardship)

    return render_template(
        "list_accounts.html",
        title = "List accounts",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        development_mode = development_mode,
        logged_in = logged_in,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,

        # List of (nested) dictionaries for display in "home.html":
        identities = identities,
        secids = secids,
        stewardships = stewardships
     )








#==============================================================================
# Payment optionspage (first version).
#
# This is an alternative view of the payment options available to that shown in
# the login landing page ("/home"). This view shows a list of payment options
# arranged alphabetically by *currency* and *identity*.
#
# This view is still too cluttered so will be replaced by a two-stage view
# comprising
# (1) "/currency/options" listing the currencies available to this *agent*, and
# (2) "/accounts_available" listing the *accounts* available in the *currency*
#     selected from the "/currency/options" list, each along with the current
#     balance and its owner (one of this *agent*'s identities').

@app.route("/payment_options", methods = ["GET", "POST"])
@login_required
def payment_options():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "payment_options"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
    group = "home" # Used to control top menu behaviour.

    namespace_steward = False

    currency_steward = False

    paying = False

    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    # The user logs in as the *primid*, even if indirectly as one of its
    # *secid*s, but once logged in will see all of its *identities* along with
    # a list of *accounts* belonging to each. The user will also see a list of
    # entities over which it holds/shares stewardship.

    stewardships_list, m = list_stewardships(primary_identity_fph)

    # Since a user may have *accounts* scattered across an arbitrary number of
    # *namespaces*, it is necessary to maintain a list of these:

    # A full list of *identities* is compiled, with the *primid* first and the
    # *secids* arranged alphabetically:
    identities_list = list_secids(primary_identity_fph)
    identities_list.sort()
    identities_list.insert(0, primary_identity_fph)

    # We now need a list of the *currencies* available to these *identities*
    # along with a list of *accounts* in each.

    # In order to accommodate the table in the width of a typical phone screen,
    # the table needs to be divided into sections (one for each *currency*).
    # A single table is used (rather than a separate table for each *currency*)
    # in order to keep the column widths consistent.
    #
    # In due course, the table will be replaced with suitable <div> elements,
    # but that is not an urgent priority.

    currency_changed = True     # To be changed to false whenever consecutive
    previous_currency_fph = ""  # option rows are found to have the same
                                # currency. This transition is then indicated
                                # in the dictionary passed to the template.

    payment_options_list = [] # a list of dictionaries to be iterated
    for id_fph in identities_list:

        id_fph, \
        id_hrns, \
        etype, \
        m = identify_entity(id_fph)
        if m: # (this should never happen)
            flash(m)
            return redirect("/home")

        if etype == "primid":
            id_type = "login identity"
        elif etype == "secid":
            id_type = "alias"
        else:
            id_type = "poltergeist" # something to be investigated

        accounts_list, m = list_agent_accounts(id_fph)
        if m: # (this should never happen)
            flash(m)
            return redirect("/home")
        accounts_list.sort()
        for a_fph in accounts_list:

            # fetch *account* details:
            c_fph, \
            a_owner_fph, \
            a_balance, \
            a_volume, \
            m = get_account_specific_properties(a_fph)
            a_balance_d = integer_to_money_format(a_balance)

            isneg = (a_balance < 0)

            # Fetch *currency* details:
            c_fph, \
            c_hrns, \
            c_prefix, \
            c_suffix, \
            c_default_account_name, \
            c_stewards_list, \
            m = get_currency_specific_properties(c_fph)

            currency_changed = (c_fph != previous_currency_fph)

            p = {} # a (*currency", *identity*, *account*) triplet
            p["currency"] = {}
            p["currency"]["currency_changed"] = currency_changed
            p["currency"]["fph"] = c_fph
            p["currency"]["hrns"] = fph_to_hrns(c_fph)
            #p["currency"]["primid_is_c_steward"] = primid_currency_steward
            if c_fph in stewardships_list:
                p["currency"]["primid_is_c_steward"] = True
            else:
                p["currency"]["primid_is_c_steward"] = False
            p["currency"]["identity"] = {}
            p["currency"]["identity"]["fph"] = id_fph
            p["currency"]["identity"]["hrns"] = fph_to_hrns(id_fph)
            p["currency"]["identity"]["type"] = id_type
            p["currency"]["identity"]["account"] = {}
            p["currency"]["identity"]["account"]["fph"] = a_fph
            p["currency"]["identity"]["account"]["hrns"] = fph_to_hrns(a_fph)
            p["currency"]["identity"]["account"]["owner_fph"] = a_owner_fph
            p["currency"]["identity"]["account"]["balance"] = a_balance_d
            p["currency"]["identity"]["account"]["isneg"] = (a_balance < 0)
            p["currency"]["identity"]["account"]["prefix"] = c_prefix
            p["currency"]["identity"]["account"]["suffix"] = c_suffix
            payment_options_list.append(p)

            previous_currency_fph = c_fph

    # We now have a list of dictionaries to be iterated that can be iterated
    # by the Jinja2 template.

    return render_template(
        "payment_options.html",
        title = "payment options",
        page = page,
        group = group,
        hub_mode = hub_mode,
        development_mode = development_mode,
        version = get_version(),
        logged_in = logged_in,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        # List of (nested) dictionaries for "payment_options.html":
        payment_options_list = payment_options_list
    )

#==============================================================================
# Payment optionspage (second version).
#
# This is an alternative view of the payment options available to that shown in
# the login landing page ("/home"). This view shows a sorted list of the
# *currencies* available to this *agent*.
#
# This is the first of a two-stage view comprising
# (1) "/currency/options" listing the currencies available to this *agent*, and
# (2) "/accounts_available" listing the *accounts* available in the *currency*
#     selected from the "/currency/options" list, each along with the current
#     balance and its owner (one of this *agent*'s identities').
#
# First stage:

@app.route("/currency/options", methods = ["GET", "POST"])
@login_required
def currency_options():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "currency_options"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    # The user logs in as the *primid*, even if indirectly as one of its
    # *secid*s, but once logged in will see all of its *identities* along with
    # a list of *accounts* belonging to each. The user will also see a list of
    # entities over which it holds/shares stewardship.

    stewardships_list, m = list_stewardships(primary_identity_fph)

    # Since a user may have *accounts* scattered across an arbitrary number of
    # *namespaces*, it is necessary to maintain a list of these:

    # A full list of *identities* is compiled, with the *primid* first and the
    # *secids* arranged alphabetically:
    identities_list = list_secids(primary_identity_fph)
    identities_list.sort()
    identities_list.insert(0, primary_identity_fph)

    # We now need a list of the *currencies* available to these *identities*
    # along with a list of *accounts* in each.

    # In order to accommodate the table in the width of a typical phone screen,
    # the table needs to be divided into sections (one for each *currency*).
    # A single table is used (rather than a separate table for each *currency*)
    # in order to keep the column widths consistent.
    #
    # In due course, the table will be replaced with suitable <div> elements,
    # but that is not an urgent priority.

    currencies_available = []   # for use by "/currency/options"
                                # This list will be passed to the template.
                                # The *currency* selected from that list will
                                # then determine which collection of *accounts*
                                # (to whichever of this *agent*'s *identities*
                                # each belongs) will be listed in the next view
                                # "/account/options".

    currencies_list = []        # for use by "/account/options"

    payment_options = []

    for id_fph in identities_list:

        id_fph, \
        id_hrns, \
        etype, \
        m = identify_entity(id_fph)
        if m: # (this should never happen)
            flash(m)
            return redirect("/home")

        if etype == "primid":
            id_type = "login identity"
        elif etype == "secid":
            id_type = "alias"
        else:
            id_type = "poltergeist" # something to be investigated

        accounts_list, m = list_agent_accounts(id_fph)
        if m: # (this should never happen)
            flash(m)
            return redirect("/home")
        accounts_list.sort()
        for a_fph in accounts_list:

            # fetch *account* details:
            c_fph, \
            a_owner_fph, \
            a_ahid_fph, \
            a_balance, \
            a_volume, \
            m = get_account_specific_properties(a_fph)
            a_balance_d = integer_to_money_format(a_balance)

            isneg = (a_balance < 0)

            # Fetch *currency* details:
            c_fph, \
            c_hrns, \
            c_prefix, \
            c_suffix, \
            c_default_account_name, \
            c_stewards_list, \
            m = get_currency_specific_properties(c_fph)

            # For the "/currency/options" page we need a list of *currencie*
            # available to this *agent*:
            c = {}
            c["fph"] = c_fph
            c["hrns"] = fph_to_hrns(c_fph)
            if c_fph in stewardships_list:
                c["primid_is_c_steward"] = True
            else:
                c["primid_is_c_steward"] = False
            if not (c in currencies_list):
                currencies_list.append(c)

            currencies_available.append(c_fph)

            # For the "/account/options" page we need a full dictionary of the
            # *accounts* available in each *currency* since we do not yet know
            # which will be selected from those displayed in the
            # "/currency/options" page:
            p = {} # a (*currency", *identity*, *account*) triplet
            p["currency"] = {}
            p["currency"]["fph"] = c_fph
            p["currency"]["hrns"] = fph_to_hrns(c_fph)
            if c_fph in stewardships_list:
                p["currency"]["primid_is_c_steward"] = True
            else:
                p["currency"]["primid_is_c_steward"] = False
            p["currency"]["identity"] = {}
            p["currency"]["identity"]["fph"] = id_fph
            p["currency"]["identity"]["hrns"] = fph_to_hrns(id_fph)
            p["currency"]["identity"]["type"] = id_type
            p["currency"]["identity"]["account"] = {}
            p["currency"]["identity"]["account"]["fph"] = a_fph
            p["currency"]["identity"]["account"]["hrns"] = fph_to_hrns(a_fph)
            p["currency"]["identity"]["account"]["owner_fph"] = a_owner_fph
            p["currency"]["identity"]["account"]["balance"] = a_balance_d
            p["currency"]["identity"]["account"]["isneg"] = (a_balance < 0)
            p["currency"]["identity"]["account"]["prefix"] = c_prefix
            p["currency"]["identity"]["account"]["suffix"] = c_suffix

            payment_options.append(p)

            #print("currency available: " + fph_to_hrns(c_fph))

            #print("payment option: ", end="")
            #print(p)

    # We now have a list of *currencies* (each as a dictionary to be passed to
    # the "/currency/options" view).
    #
    # We also have a dictionary, with the *currency* FPH as the top-level key,
    # to be interated in the "/account/options" view which follows after the
    # selection of a *currency* from those listed in the  "/currency/options"
    # view. Both the selected *currency* and the full dictionary of *account*
    # options are needed by the "/account/options" view, these must be passed
    # across from the first view to the second. The simplest approach might be
    # to use the Flask  session[ ]  dictionary.
    session_save_currencies_available(currencies_available, payment_options)
    #session["payment_options"] = pickle.dumps(payment_options)

    #print("session_save_currencies_available( ) done")


    # Although the *currency* selected is passed via the URL slug, we must
    # still be able to check that it is a valid option for the *agent* in this
    # session, so it is added to the  session[ ]  dictionary:
    #session["currencies_available"] = pickle.dumps(currencies_available)

    # NB, the p dictionary may be quite large so we need to avoid passing it
    # upon every subsequent page request. Therefore it should be cleared from
    # session[ ]  as soon as it has been used by the "/account/options" view.

    return render_template(
        "currency_options.html",
        title = "currency options",
        page = page,
        group = group,
        development_mode = development_mode,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        currencies_list = currencies_list # list of *currencies* available
     )

#------------------------------------------------------------------------------
# Second stage:
#
# "/account/options" (always follow immediately after "/currency/options")

@app.route("/account/options/<currency_fph>", methods = ["GET", "POST"])
@login_required
def account_options(currency_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "payment_options"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    currencies_available, \
    payment_options_list, \
    m = session_retrieve_currencies_available()
    if m:
        flash(m)
    if m == "Payment options unavailable":
        #flash(m)
        return redirect("/currency/options")
    #m = session_retrieve_payment_options()

    #print("session_retrieve_currencies_available() done")

    #for c_fph in currencies_available:
    #    print("currency available: " + fph_to_hrns(c_fph))

    #for p in payment_options_list:
    #    print("payment option: ", end="")
    #    print(p)


    currency_selected_hrns = fph_to_hrns(currency_fph)

    logged_in = current_user.is_authenticated # for menu display control

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    return render_template(
        "payment_options.html",
        title = "account options",
        page = page,
        group = group,
        development_mode = development_mode,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        # The *currency* selected from the list of *currency* options:
        currency_selected_hrns = currency_selected_hrns,
        payment_options_list = payment_options_list
     )

#==============================================================================
# account details page --------------------------------------------------------

# Note:
#
# Change endpoint from
#   /account/<account_fph>
# to
#   /pay/account/<account_fph>
# and (possibly) change
#   def account(account_fph)
# to
#   def pay_account(account_fph)
# (although that may introduce complications, so don't leap without looking
# very thoroughly).
#
# Also dd
#   /pay/identity
# or
#   /pay_identity

@app.route("/account/<payer_account_fph>/<payee_account_fph>/<owner_fph>",
           methods = ["GET", "POST"])
@login_required
def account(payer_account_fph, payee_account_fph, owner_fph = None):

    if owner_fph is not None:
        account_owner_fph, \
        account_owner_hrns, \
        etype, \
        m = identify_entity(owner_fph)
        if m:
            flash(m)
            return redirect("/home")
        if account_owner_fph == "":
            flash("Invalid account owner in URL")
            return redirect("/home")

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "account"
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    previous_page = session["previous_page"]
    session["previous_page"] = page

    # The *primid* (or its alias *secid*) logged in currently:
    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    # (This uses the identify_entity( ) function:)
    #primary_identity_type = fph_to_display_type(primary_identity_fph)

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

   # If a payer *account* has been specified (by FPH) in the URL slug
    payer_account_fph, \
    payer_account_hrns, \
    etype, \
    m = identify_entity(payer_account_fph)
    if m:
        flash(m)

    if not payer_account_fph:
        flash("The FPH in the URL cannot be identified.")
        return redirect("/account")
    elif etype !=  "account":
        flash("The FPH in the URL does not identify an account.")
        return redirect("/home")

    payee_account_known = False
    if payee_account_fph is not None:
        # A pseudo-FPH is used where only the payer account FPH is provided:
        if payee_account_fph == "0": # (obviously not a valid FPH)
            payee_account_fph = ""
            payee_account_hrns = ""
        else:
            # If a payee *account* has been specified (by FPH) in the URL slug
            payee_account_fph, \
            payee_account_hrns, \
            etype, \
            m = identify_entity(payee_account_fph)
            if m:
                flash(m)
            if payee_account_fph:
                payee_account_known = True
    else:
        payee_account_fph = ""
        payee_account_hrns = ""

    payer_currency_fph, \
    payer_owner_fph, \
    payer_ahid_fph, \
    payer_balance, \
    volume, \
    m = get_account_specific_properties(payer_account_fph)

    if m:
        flash(m)
        return redirect("/account")

    account_balance_is_negative = (payer_balance < 0)

    #currency_hrns = fph_to_hrns(payer_currency_fph)
    currency_fph, \
    currency_hrns, \
    currency_prefix, \
    currency_suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_specific_properties(payer_currency_fph)

    # If control reaches this point, it has been established that the *account*
    # specified in the URL slug belongs to the current user.
    #
    form = PaymentToAccountForm()
    if form.validate_on_submit():

        payee_account_identifier = form.to_account_id.data # HRNS or FPH
        amount_entered = form.amount.data
        annotation = form.annotation.data

        amount = int(round(float(amount_entered)*100))

        if (payee_account_identifier is not None) and payee_account_identifier:
            payee_account_fph, \
            payee_account_hrns, \
            etype, \
            m = identify_entity(payee_account_identifier)

            if etype !=  "account":
                flash(payee_account_identifier + " is not an account")
                return redirect("/account/" + payer_account_fph)

        if payee_account_fph == payer_account_fph:
            flash("An account cannot pay to itself")
            return redirect("/account/" + payer_account_fph)

        payee_currency_fph, \
        payee_owner_fph, \
        payee_ahid_fph, \
        payee_balance, \
        volume, \
        m = get_account_specific_properties(payee_account_fph)

        if payee_currency_fph != payer_currency_fph:
            flash(
                "The payer account  " + payer_account_hrns + "  and the " \
                + "payee account  " + payee_account_hrns \
                + "  are not in the same currency."
            )
            return redirect(
                "/account/" + payer_account_fph + payer_account_fph
            )

        # If control reaches this point, the two *accounts* are in the same
        # *currency* so the payment can be made:
        m = payment(payer_account_fph, payee_account_fph, amount, annotation)
        if m:
            flash(m)
            #return redirect("/account/" + payer_account_fph)
            #return redirect("/account/" + payer_account_fph)
            return redirect("/home")

        payer_currency_fph, \
        payer_owner_fph, \
        payer_ahid_fph, \
        payer_balance, \
        volume, \
        m = get_account_specific_properties(payer_account_fph)

        payee_currency_fph, \
        payee_owner_fph, \
        payee_ahid_fph, \
        payee_balance, \
        volume, \
        m = get_account_specific_properties(payee_account_fph)

        flash(
            "Payment submitted: " \
            + currency_prefix \
            + integer_to_money_format(amount) \
            + currency_suffix
        )
        return redirect("/home")

    return render_template(
        "account.html",
        title = "Account",
        form = form,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        account_owner_hrns = account_owner_hrns,
        payer_account_fph = payer_account_fph,
        payer_account_hrns = payer_account_hrns,
        payee_account_known = payee_account_known,
        payee_account_fph = payee_account_fph,
        payee_account_hrns = payee_account_hrns,
        account_balance = integer_to_money_format(payer_balance),
        account_balance_is_negative = account_balance_is_negative,
        logged_in = logged_in,
        currency_prefix = currency_prefix,
        currency_suffix = currency_suffix,
        currency_fph = currency_fph,
        currency_hrns = currency_hrns,
        payer_balance = payer_balance
    )

# ==============================================================================
#
@app.route("/pay_to_ahid/<payer_ahid_fph>/<payment_currency_fph>",
           methods = ["GET", "POST"])
@login_required
def pay_ahid(payer_ahid_fph, payment_currency_fph):

    payer_ahid_fph, \
    payer_ahid_hrns, \
    etype, \
    m = identify_entity(payer_ahid_fph)

    if payer_ahid_fph == "":
        flash("Invalid payer account-holder")
        return redirect("/home_ahc")

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(payment_currency_fph)

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "pay_ahid"
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    working_identity_fph = primary_identity_fph
    working_identity_hrns = primary_identity_hrns
    working_identity_type = primary_identity_type

    form = SpecifyPayeeAccountHolderForm()
    if form.validate_on_submit():
        payee_ahid_fph, \
        payee_ahid_hrns, \
        etype, \
        m = identify_entity(form.payee_ahid.data) # HRNS or FPH
        if m:
            flash(m)
            return redirect(
                       "/pay_to_ahid/" + payer_ahid_fph + "/" + currency_fph
                   )
        if payee_ahid_fph == "":
            flash("The specified account-holder does not exist")
            return redirect(
                       "/pay_to_ahid/" + payer_ahid_fph + "/" + currency_fph
                   )
        if not get_ahid_primid(payee_ahid_hrns):
        #if etype != "ahid":
            flash("The payee specified is not an account-holder")
            return redirect(
                       "/pay_to_ahid/" + payer_ahid_fph + "/" + currency_fph
                   )

#        currency_fph, \
#        currency_hrns, \
#        etype, \
#        m = identify_entity(form.currency_id.data)

        #amount = form.amount.data


        amount = int(round(float(form.amount.data)*100))



#        print("amount = ", end="")
#        print(amount)
#        if not re_pvalue.match(amount):
#            flash("The payment amount submitted is invalid")
#            return redirect(
#                       "/pay_to_ahid/" + payer_ahid_fph + "/" + currency_fph
#                   )

        annotation = form.annotation.data


        # MAKE PAYMENT HERE
        m = ah_payment(
                payer_ahid_hrns,
                payee_ahid_hrns,
                currency_hrns,
                amount,
                annotation
            )

        if hub_mode == "omtrad":
            return redirect("/home_ahc")
        else:
            return redirect("/home")

    return render_template(
        "pay_to_ahid.html",
        title = "Make a payment to an account-holder",
        page = page,
        group = group,
        form = form,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        payer_ahid_hrns = payer_ahid_hrns,
        currency_hrns = currency_hrns
    )




# ==============================================================================
#
@app.route("/pay_to_account", methods = ["GET", "POST"])
@login_required
def pay_account():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "pay_account"
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    form = SpecifyPayeeAccountForm()
    if form.validate_on_submit():
        payee_account_fph, \
        payee_account_hrns, \
        etype, \
        m = identify_entity(form.to_account_id.data) # HRNS or FPH
        if m:
            flash(m)
            return redirect("/pay_to_account")
        if payee_account_fph == "":
            return redirect("/pay_to_account")

        return redirect("/select_payer_account/" + payee_account_fph)

    return render_template(
        "pay_to_account.html",
        title = "Make a payment to an account",
        page = page,
        group = group,
        form = form,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type
    )


#
# ==============================================================================
#
@app.route("/journal/<ahid_fph>/<currency_fph>", methods = ["GET", "POST"])
@login_required
def journal(ahid_fph, currency_fph):

    ahid_fph, \
    ahid_hrns, \
    etype, \
    m = identify_entity(ahid_fph)
    if ahid_fph == "":
        flash("Invalid account-holder")
        return redirect("/home_ahc")

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_fph)
    if currency_fph == "":
        flash("Invalid currency")
        return redirect("/home_ahc")

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "journal"
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    working_identity_fph = primary_identity_fph
    working_identity_hrns = primary_identity_hrns
    working_identity_type = primary_identity_type

    account_fph, \
    primid_fph, \
    m = retrieve_pairing_account_fph(ahid_hrns, currency_fph)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified currency:
        cursor.execute(
            """
            SELECT timestamp,
                   payment_id,
                   payer_fph,
                   payee_fph,
                   currency_fph,
                   amount,
                   payer_balance,
                   payee_balance,
                   annotation
            FROM payments
            WHERE (payer_fph = ? OR payee_fph = ?) and (currency_fph = ?)
            """,
            (ahid_fph, ahid_fph, currency_fph)
        )
        all_payments = cursor.fetchall()
        cursor.close()
    if all_payments is None:
        flash("There are no journal entries to display")
        return redirect("/home_ahc")

    journal_rows = []
    for payment in all_payments:
        p = list(payment)
        timestamp = p[0]
        dt = timestamp.split(" ")
        p_date = dt[0]
        p_time_ = dt[1].split(":")
        p_time_.pop()
#        print(p_time_)
        p_time = ":".join(p_time_)
#        print(p_time)


        payment_id = str(p[1]).zfill(8)
        payer_fph = p[2]
        payee_fph = p[3]
        currency_fph = p[4]
        amount = integer_to_money_format(p[5])
        payer_balance_negative = (p[6] < 0)
        payer_balance = integer_to_money_format(p[6])
        payee_balance_negative = (p[7] < 0)
        payee_balance = integer_to_money_format(p[7])
        annotation = p[8]
        # The results are now put into a list of dictionaries to be fed to the
        # template:
        journal_row = {}
        journal_row["date"] = p_date
        journal_row["time"] = p_time
        journal_row["xid"] = payment_id
        if payer_fph == ahid_fph: # payment
            journal_row["type"] = "payment"
            journal_row["amount"] = amount
            journal_row["other_ahid_hrns"] = fph_to_hrns(payee_fph)
            journal_row["balneg"] = payer_balance_negative
            journal_row["balance"] = payer_balance
        elif payee_fph == ahid_fph: # receipt
            journal_row["type"] = "receipt"
            journal_row["amount"] = amount
            journal_row["other_ahid_hrns"] = fph_to_hrns(payer_fph)
            journal_row["balneg"] = payee_balance_negative
            journal_row["balance"] = payee_balance
        else: # this should never happen
            journal_row["type"] = ""
            journal_row["amount"] = ""
            journal_row["other_ahid_hrns"] = ""
            journal_row["balneg"] = ""
            journal_row["balance"] = ""
        journal_row["annotation"] = annotation
#        journal_rows.append(journal_row)
        journal_rows.insert(0, journal_row)

    return render_template(
        "transaction_journal_ahc.html",
        title = "Display transaction journal",
        page = page,
        group = group,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        ahid_hrns = ahid_hrns,
        currency_hrns = currency_hrns,
        journal_rows = journal_rows,
        account_fph = account_fph
    )

#=============================================================================
#TEST STUFF

def print_payments_session_variables():
    #
    # TEST STUFF
    for key in [
                    "payee_identity_fph",
                    "payment_currency_fph",
                    "number_of_payer_accounts",
                    "number_of_payee_accounts",
                    "payer_account_fph",
                    "payee_account_fph"
               ]:
        print(key + " :: ", end="")
        if key in session:
            print(session[key])
        else:
            print()



#=============================================================================
# Make a payment to an *agent*+*currency* rather than to an *account*. This
# endpoint is reached when a "pay" link is clicked in the "/home" screen table
# (in )"slate_simple" mode).
#
@app.route("/pay/from/<payer_account_fph>", methods = ["GET", "POST"])
@login_required
def pay_from_account_to_agent(payer_account_fph = None):

    if payer_account_fph is None:
        flash("No payer account specified in URL")
        return redirect("/home")
    payer_account_fph, \
    payer_account_hrns, \
    etype, \
    m = identify_entity(payer_account_fph)
    if m:
        flash(m)
        return redirect("/home")
    if payer_account_fph == "":
        flash("Invalid FPH in URL")
        return redirect("/home")
    if etype != "account":
        flash("Entity type of FPH in URL is not account")
        return redirect("/home")

    #payment_currency_fph = get_account_currency(payer_account_fph)
    payment_currency_fph, \
    payer_account_owner_fph, \
    payer_account_ahid_fph, \
    payer_account_balance, \
    volume, \
    m = get_account_specific_properties(payer_account_fph)

    if payer_account_balance < 0:
        payer_account_balance_negative = True
    else:
        payer_account_balance_negative = False

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "payer_currency_known"
    group = "home"
    logged_in = current_user.is_authenticated

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    #print("previous_page = " + previous_page)

    if (previous_page != "home") and (previous_page != "payer_currency_known"):
        flash("Incorrect page succession")
        return redirect("/home")

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    # (1) Clear any existing data from the session dictionary:
    if "payee_identity_fph" in session:
        session.pop("payee_identity_fph")
    if "payment_currency_fph" in session:
        session.pop("payment_currency_fph")
    if "number_of_payer_accounts" in session:
        session.pop("number_of_payer_accounts")
    if "number_of_payee_accounts" in session:
        session.pop("number_of_payee_accounts")
    if "payer_account_fph" in session:
        session.pop("payer_account_fph")
    if "payee_account_fph" in session:
        session.pop("payee_account_fph")
    # (2) Clear any existing data from the session database:
    remove_slate_session_data()

    session["payment_currency_fph"] = payment_currency_fph
    session["payer_account_fph"] = payer_account_fph


    # We now know both the payer *account* and the payment *currency*, so now
    # we need to acquire the *identity* form data:
    form = SpecifyPayeeAgentForm()
    if form.validate_on_submit():

        payee_identity_fph, \
        payee_identity_hrns, \
        etype, \
        m = identify_entity(form.to_identity_id.data) # HRNS or FPH
        if m:
            flash(m)
            return redirect("/home")
        if payee_identity_fph == "":
            flash("The identity is invalid")
            return redirect("/home")
        session["payee_identity_fph"] = payee_identity_fph

        payer_options = []
        payer_options.append(payer_account_fph) # single option already known

        # Next we need to find the payee *accounts* in the specified
        # *currency*:
        payee_accounts, m = list_agent_accounts(payee_identity_fph)
        if payer_account_fph in payee_accounts:
            payee_accounts.remove(payer_account_fph)
        if len(payee_accounts) == 0:
            flash("There are no payee account options.")
            return redirect("/home")
        payee_options = []
        for payee_account_fph in payee_accounts:
            account_currency_fph = get_account_currency(payee_account_fph)
            if account_currency_fph == payment_currency_fph:
                payee_options.append(payee_account_fph)

        # These lists of payer and payee *account* options are now saved for
        # use in the selection stages:
        session_save_payment_options(payer_options, payee_options)

        return redirect("/pay/select/payee/" + payer_account_fph) # next page

    return render_template(
        "pay_agent_in_known_currency.html",
        title = "Make a payment to an agent in known currency",
        page = page,
        group = group,
        form = form,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        payer_account_hrns = fph_to_hrns(payer_account_fph),
        payer_identity_hrns = fph_to_hrns(payer_account_owner_fph),
        payment_currency_hrns = fph_to_hrns(payment_currency_fph),
        payer_account_balance = integer_to_money_format(payer_account_balance),
        payer_account_balance_negative = payer_account_balance_negative
    )


#=============================================================================
# Make a payment to an *agent*+*currency* rather than to an *account*. This
# endpoint is reached when the "pay" link is clicked in "slate_minimal" mode.
#
# Added 2025-03-17:
@app.route("/pay/agent/direct/<payer_currency_fph>/<payer_identity_fph>",
           methods = ["GET", "POST"]
          )
@login_required
def pay_agent_direct(payer_currency_fph, payer_identity_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "pay_agent_direct"
    group = "home"
    logged_in = current_user.is_authenticated

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    # Every process of payment to *identity*+*currency* begins here, so it is
    # only here where the relevant persistent data needs to be cleared out.
    #
    # (1) Clear any existing data from the session dictionary:
    if "payee_identity_fph" in session:
        session.pop("payee_identity_fph")
    if "payment_currency_fph" in session:
        session.pop("payment_currency_fph")
    if "number_of_payer_accounts" in session:
        session.pop("number_of_payer_accounts")
    if "number_of_payee_accounts" in session:
        session.pop("number_of_payee_accounts")
    if "payer_account_fph" in session:
        session.pop("payer_account_fph")
    if "payee_account_fph" in session:
        session.pop("payee_account_fph")
    # (2) Clear any existing data from the session database:
    remove_slate_session_data()

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(payer_currency_fph)
    if m:
        flash(m)
        return redirect("/pay/agent")
    if currency_fph == "":
        flash("The currency cannot be identified")
        return redirect("/pay/agent")
    session["payment_currency_fph"] = currency_fph

    payer_identity_fph, \
    payer_identity_hrns, \
    etype, \
    m = identify_entity(payer_identity_fph)

    # Now we need to acquire the payee *identity* and *amount* form data:
    form = PayeeCurrencyAmountPaymentForm()
    if form.validate_on_submit():

        #print("form validated")

        payee_identity_fph, \
        payee_identity_hrns, \
        etype, \
        m = identify_entity(form.to_identity_id.data) # HRNS or FPH
        if m:
            flash(m)
            return redirect("/pay/agent")
        if payee_identity_fph == "":
            flash("The identity is invalid")
            return redirect("/pay/agent")
        session["payee_identity_fph"] = payee_identity_fph

        #print("payee = " + payee_identity_hrns)

        # First we need to find the payer *accounts* in the specified
        # *currency*:
        payer_accounts, m = list_agent_accounts(working_identity_fph)
        payer_options = []
        for payer_account_fph in payer_accounts:
            account_currency_fph = get_account_currency(payer_account_fph)
            if account_currency_fph == currency_fph:
                payer_options.append(payer_account_fph)

        # Next we need to find the payee *accounts* in the specified
        # *currency*:
        payee_accounts, m = list_agent_accounts(payee_identity_fph)
        payee_options = []
        for payee_account_fph in payee_accounts:
            account_currency_fph = get_account_currency(payee_account_fph)
            if account_currency_fph == currency_fph:
                payee_options.append(payee_account_fph)

        # These lists of payer and payee *account* options are now saved for
        # use in the selection stages:
        session_save_payment_options(payer_options, payee_options)

        # Unless both the payee and the payee have at least one *account* in
        # this *currency*, the payment cannpt be made.
        if len(payer_options) == 0:
            flash("The payer has no accounts in the specified currency")
            return redirect("/pay/agent")
        if len(payee_options) == 0:
            flash("The payee has no accounts in the specified currency")
            return redirect("/pay/agent")

#        if len(payer_options) == 1:
#            print("The payer has one account in this currency")
#        if len(payee_options) == 1:
#            print("The payee has one account in this currency")



        # If both the payer and the payee have only one *account* in this
        # *currency*, the payment can be made immediately.

        # If either the payer or the payee has more than one *account* in this
        # *currency* a selection must be made. Therefore the list of options
        # must be passed to one or both intermediate form/endpoint to allow the
        # selection of *accounts*.
#        return redirect("/home") # next page
        #return redirect("/pay/select/payer") # next page

        amount_entered = form.amount.data
        annotation = form.annotation.data

        amount = int(round(float(amount_entered)*100))

        m = payment(payer_account_fph, payee_account_fph, amount, annotation)
        if m:
            flash(m)
            #print(m)
            return redirect("/home")

#        print("Payment made")

        payer_currency_fph, \
        payer_owner_fph, \
        payer_ahid_fph, \
        payer_balance, \
        payer_volume, \
        m = get_account_specific_properties(payer_account_fph)

        payee_currency_fph, \
        payee_owner_fph, \
        payee_ahid_fph, \
        payee_balance, \
        payee_volume, \
        m = get_account_specific_properties(payee_account_fph)

        flash(
            "Payment submitted: " \
            + currency_prefix \
            + integer_to_money_format(amount) \
            + currency_suffix
        )

        # Clear out any existing session data relating to payments:
        if "payee_identity_fph" in session:
            session.pop("payee_identity_fph")
        if "payment_currency_fph" in session:
            session.pop("payment_currency_fph")
        if "number_of_payer_accounts" in session:
            session.pop("number_of_payer_accounts")
        if "number_of_payee_accounts" in session:
            session.pop("number_of_payee_accounts")
        if "payer_account_fph" in session:
            session.pop("payer_account_fph")
        if "payee_account_fph" in session:
            session.pop("payee_account_fph")

        return redirect("/home")

    return render_template(
        "pay_agent_direct.html",
        title = "Make a payment to an agent",
        page = page,
        group = group,
        form = form,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        payer_identity_hrns = payer_identity_hrns,
        currency_hrns = currency_hrns
    )








#=============================================================================
# Make a payment to an *agent*+*currency* rather than to an *account*. This
# endpoint is reached when the "pay to agent" button is clicked.
#
@app.route("/pay/agent/", methods = ["GET", "POST"])
@login_required
def pay_agent():

    # The payee will have specified an *identity* and a *currency*, both of
    # which are entered into the form below, so here we need to take the
    # followig steps:
    # (1) List the *accounts* that the payer has in this *currency*.
    # (1.1) If none, display explanatory message and return to home.
    # (1.2) If only one, no selection will be necessary.
    # (1.3) If more than one, it will be necessary to choose from the options.
    # (2) List the *accounts* that the payee has in this *currency*.
    # (2.1) If none (unlikely), display explanatory message and return to home.
    # (2.2) If only one, no selection will be necessary.
    # (2.3) If more than one, it will be necessary to choose from the options.
    #       This situation may arise if the payee has specified only an
    #       *identity* and a *currency* but not an *account* and cannot be
    #       be contacted for clarification.
    #
    # If (1.2) and (2.2), pass control immediately to payment form.
    #
    # If (1.3) or (2.3), pass control to intermediate *account* selection form
    # before passing control to payment form.
    #
    # In payment form, enter amount and annotation beform confirming payment.
    # The messaging system will inform the payee that the payment has been made
    # and to which *account*.

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()

    page = "pay_agent"
    group = "home"
    logged_in = current_user.is_authenticated

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    # Every process of payment to *identity*+*currency* begins here, so it is
    # only here where the relevant persistent data needs to be cleared out.
    #
    # (1) Clear any existing data from the session dictionary:
    if "payee_identity_fph" in session:
        session.pop("payee_identity_fph")
    if "payment_currency_fph" in session:
        session.pop("payment_currency_fph")
    if "number_of_payer_accounts" in session:
        session.pop("number_of_payer_accounts")
    if "number_of_payee_accounts" in session:
        session.pop("number_of_payee_accounts")
    if "payer_account_fph" in session:
        session.pop("payer_account_fph")
    if "payee_account_fph" in session:
        session.pop("payee_account_fph")
    # (2) Clear any existing data from the session database:
    remove_slate_session_data()

    # Now we need to acquire the *identity* and *account* form data:
    form = SpecifyPayeeAgentAndCurrencyForm()
    if form.validate_on_submit():

        payee_identity_fph, \
        payee_identity_hrns, \
        etype, \
        m = identify_entity(form.to_identity_id.data) # HRNS or FPH
        if m:
            flash(m)
            return redirect("/pay/agent")
        if payee_identity_fph == "":
            flash("The identity is invalid")
            return redirect("/pay/agent")
        session["payee_identity_fph"] = payee_identity_fph

        currency_fph, \
        currency_hrns, \
        etype, \
        m = identify_entity(form.currency_id.data)
        if m:
            flash(m)
            return redirect("/pay/agent")
        if currency_fph == "":
            flash("The currency cannot be identified")
            return redirect("/pay/agent")
        session["payment_currency_fph"] = currency_fph

        # First we need to find the payer *accounts* in the specified
        # *currency*:
        payer_accounts, m = list_agent_accounts(working_identity_fph)
        payer_options = []
        for payer_account_fph in payer_accounts:
            account_currency_fph = get_account_currency(payer_account_fph)
            if account_currency_fph == currency_fph:
                payer_options.append(payer_account_fph)

        # Next we need to find the payee *accounts* in the specified
        # *currency*:
        payee_accounts, m = list_agent_accounts(payee_identity_fph)
        payee_options = []
        for payee_account_fph in payee_accounts:
            account_currency_fph = get_account_currency(payee_account_fph)
            if account_currency_fph == currency_fph:
                payee_options.append(payee_account_fph)

        # These lists of payer and payee *account* options are now saved for
        # use in the selection stages:
        session_save_payment_options(payer_options, payee_options)

        # Unless both the payee and the payee have at least one *account* in
        # this *currency*, the payment cannpt be made.
        if len(payer_options) == 0:
            flash("The payer has no accounts in the specified currency")
            return redirect("/pay/agent")
        if len(payee_options) == 0:
            flash("The payee has no accounts in the specified currency")
            return redirect("/pay/agent")

        # If both the payer and the payee have only one *account* in this
        # *currency*, the payment can be made immediately.

        # If either the payer or the payee has more than one *account* in this
        # *currency* a selection must be made. Therefore the list of options
        # must be passed to one or both intermediate form/endpoint to allow the
        # selection of *accounts*.
        return redirect("/pay/select/payer") # next page


    return render_template(
        "pay_agent_in_currency.html",
        title = "Make a payment to an agent",
        page = page,
        group = group,
        form = form,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type
    )

#------------------------------------------------------------------------------
# Select from available payer *accounts*:
#
@app.route("/pay/select/payer", methods = ["GET", "POST"])
@login_required
def select_payer_account():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()

    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated
    page = "select_account_combination_in_currency"

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
    working_identity_type = etype_to_adtype(working_identity_type)

    # The original *identity*+*currency* data are retrieved for use in the
    # template:
    #
    if not "payee_identity_fph" in session:
        flash("Error: payee_identity_fph not in session dictionary")
        return redirect("/pay/agent")
    else:
        payee_identity_hrns = fph_to_hrns(session["payee_identity_fph"])

    if not "payment_currency_fph" in session:
        flash("Error: payment_currency_fph not in session dictionary")
        return redirect("/pay/agent")
    else:
        payment_currency_hrns = fph_to_hrns(session["payment_currency_fph"])

    # The payer and payee *account* options lists are retrieved:
    payer_accounts_available, \
    payee_accounts_available, \
    m = session_retrieve_payment_options()

    # If there is only one payer *account* option, we can move straight on to
    # the payee *account* selection stage. Otherwise we need to select the
    # payer *account* from a list, in which case the selection is made by
    # clicking on a link in a page rather than by using a form. Therefore the
    # payee *account* FPH is passed in the URL:
    #
    if len(payer_accounts_available) == 1:
        payer_account_fph = payer_accounts_available[0]
        session["payer_account_fph"] = payer_account_fph
        return redirect("/pay/select/payee/" + payer_account_fph)

    # If there are no payee *accounts* available, give up:
    if len(payer_accounts_available) == 0:
        flash("There are no account options from which to pay.")
        return redirect("/home")

    #
    # Otherwise we need to select the payer *account* from a list.
    payer_account_options = []
    for payer_account_fph in payer_accounts_available:
        a = {}
        a["fph"] = payer_account_fph
        a["hrns"] = fph_to_hrns(payer_account_fph)
        payer_account_options.append(a)

    return render_template(
        "select_payer_account.html",
        title = "Select the payer account",
        page = page,
        group = group,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        payee_identity_hrns = payee_identity_hrns,
        payment_currency_hrns = payment_currency_hrns,
        payer_account_options = payer_account_options
    )

#------------------------------------------------------------------------------
# Select from available payee *accounts*:
#
@app.route("/pay/select/payee/<payer_account_fph>", methods = ["GET", "POST"])
@login_required
def select_payee_account(payer_account_fph = None):

    if payer_account_fph is None:
        flash("Payer account not specified in URL")
        return redirect("/pay/agent")

    payer_account_fph, \
    payer_account_hrns, \
    etype, \
    m = identify_entity(payer_account_fph)
    if m:
        flash(m)
    if payer_account_fph == "":
        flash("Invalid payer account specified in URL")
        return redirect("/pay/agent")
    #session["payer_account_fph"] = payer_account_fph

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()

    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated
    page = "select_account_combination_in_currency"

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
    working_identity_type = etype_to_adtype(working_identity_type)

    # The original *identity*+*currency* data are retrieved for use in the
    # template:
    #
    if not "payee_identity_fph" in session:
        flash("Error: payee_identity_fph not in session dictionary")
        return redirect("/pay/agent")
    else:
        payee_identity_hrns = fph_to_hrns(session["payee_identity_fph"])

    if not "payment_currency_fph" in session:
        flash("Error: payment_currency_fph not in session dictionary")
        return redirect("/pay/agent")
    else:
        payment_currency_hrns = fph_to_hrns(session["payment_currency_fph"])

    payer_accounts_available, \
    payee_accounts_available, \
    m = session_retrieve_payment_options()

    # If there is only one payee *account* option, we can move straight on to
    # the payment stage. Otherwise we need to select the payee *account* from a
    # list, in which case the selection is made by clicking on a link in a page
    # rather than by using a form. Therefore the payee *account* FPH is passed
    # in the URL:
    #
    if (len(payee_accounts_available) == 1):
        payee_account_fph = payee_accounts_available[0]
        session["payee_account_fph"] = payee_account_fph
        return redirect(
                    "/pay/agent/payment/" \
                    + payer_account_fph + "/" \
                    + payee_account_fph
               )

    # If there are no payee *account* options, give up:
    elif (len(payee_accounts_available) == 0):
        flash("There are no account options to which to pay.")
        return redirect("/home")


    # Otherwise we need to select the payee *account* from a list.
    payee_account_options = []
    for payee_account_fph in payee_accounts_available:
        a = {}
        a["fph"] = payee_account_fph
        a["hrns"] = fph_to_hrns(payee_account_fph)
        payee_account_options.append(a)

    return render_template(
        "select_payee_account.html",
        title = "Select the payee account",
        page = page,
        group = group,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        payee_identity_hrns = payee_identity_hrns,
        payment_currency_hrns = payment_currency_hrns,
        payer_account_fph = payer_account_fph,
        payer_account_hrns = payer_account_hrns,
        payee_account_options = payee_account_options
    )


#------------------------------------------------------------------------------
# Make the payment:
#
@app.route("/pay/agent/payment/<payer_account_fph>/<payee_account_fph>",
           methods = ["GET", "POST"]
          )
@login_required
def make_payment_between_selected_accounts(
        payer_account_fph = None,
        payee_account_fph = None
    ):

#    print_payments_session_variables() ### TESTSTUFF

    if payer_account_fph is None:
        flash("Invalid payer account in URL string")
        return redirect("/home")
    if payee_account_fph is None:
        flash("Invalid payee account in URL string")
        return redirect("/home")

    #print(">>> payer_account_fph = " + payer_account_fph)
    payer_account_fph, \
    payer_account_hrns, \
    etype, \
    m = identify_entity(payer_account_fph)
    #print("<<< payer_account_fph = " + payer_account_fph)
    if m:
        flash(m)
        #print(m)
        return redirect("/home")
    if payer_account_fph == "":
        flash("No payer account in URL string")
        return redirect("/home")

    payee_account_fph, \
    payee_account_hrns, \
    etype, \
    m = identify_entity(payee_account_fph)
    if m:
        flash(m)
        #print(m)
        return redirect("/home")
    if payee_account_fph == "":
        flash("No payee account in URL string")
        return redirect("/home")

    # Clear out any existing session data relating to payments:
    if "payee_identity_fph" in session:
        payee_identity_fph = session["payee_identity_fph"]
    if "payment_currency_fph" in session:
        payment_currency_fph = session["payment_currency_fph"]
    if "number_of_payer_accounts" in session:
        number_of_payer_accounts = session["number_of_payer_accounts"]
    if "number_of_payee_accounts" in session:
        number_of_payee_accounts = session["number_of_payee_accounts"]
    if "payer_account_fph" in session:
        payer_account_fph = session["payer_account_fph"]
    if "payee_account_fph" in session:
        payee_account_fph = session["payee_account_fph"]

    currency_fph, \
    currency_hrns, \
    currency_prefix, \
    currency_suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_specific_properties(payment_currency_fph)

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()

    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated
    page = "make_payment_between_selected_accounts"

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
    working_identity_type = etype_to_adtype(working_identity_type)

    form = PaymentAccountPairForm()
    if form.validate_on_submit():

        amount_entered = form.amount.data
        annotation = form.annotation.data

        amount = int(round(float(amount_entered)*100))

        m = payment(payer_account_fph, payee_account_fph, amount, annotation)
        if m:
            flash(m)
            #print(m)
            return redirect("/home")

        payer_currency_fph, \
        payer_owner_fph, \
        payer_ahid_fph, \
        payer_balance, \
        payer_volume, \
        m = get_account_specific_properties(payer_account_fph)

        payee_currency_fph, \
        payee_owner_fph, \
        payee_ahid_fph, \
        payee_balance, \
        payee_volume, \
        m = get_account_specific_properties(payee_account_fph)

        flash(
            "Payment submitted: " \
            + currency_prefix \
            + integer_to_money_format(amount) \
            + currency_suffix
        )

        # Clear out any existing session data relating to payments:
        if "payee_identity_fph" in session:
            session.pop("payee_identity_fph")
        if "payment_currency_fph" in session:
            session.pop("payment_currency_fph")
        if "number_of_payer_accounts" in session:
            session.pop("number_of_payer_accounts")
        if "number_of_payee_accounts" in session:
            session.pop("number_of_payee_accounts")
        if "payer_account_fph" in session:
            session.pop("payer_account_fph")
        if "payee_account_fph" in session:
            session.pop("payee_account_fph")

        return redirect("/home")

    return render_template(
        "account_pair_payment.html",
        title = "Account pair payment",
        form = form,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        payer_account_fph = payer_account_fph,
        payer_account_hrns = payer_account_hrns,
#        payee_account_known = payee_account_known,
        payee_account_fph = payee_account_fph,
        payee_account_hrns = payee_account_hrns,
        payee_identity_hrns = fph_to_hrns(payee_identity_fph),
        logged_in = logged_in,
        currency_prefix = currency_prefix,
        currency_suffix = currency_suffix,
        currency_fph = currency_fph,
        currency_hrns = currency_hrns
    )




























###############################################################################
# payment to an *agent* -- select available payer-payee *account* pair --------
#
@app.route("/select_account_combination_in_currency" \
           + "/<payee_identity_fph>/<currency_fph>", methods = ["GET", "POST"])
@login_required
def select_account_combination_in_currency(payee_identity_fph, currency_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()

    page = "select_account_combination_in_currency"
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    # In contrast to the case of paying to a known *account*, here the payee
    #*account* and the *currency* have been specified.
    #
    # Both the payer and the payee may each have several accounts in this
    # *currenccy*, so one of the available combinations must be selected.

    all_payer_accounts, m = list_agent_accounts(primary_identity_fph)
    all_payee_accounts, m = list_agent_accounts(payee_fph)

    # NB, the following is a temporary solution pending cleanup and merger:

    usable_payer_accounts = []
    for payer_account_fph in all_payer_accounts:
        if get_account_currency(payer_account_fph) == currency_fph:
            usable_payer_accounts.append(payer_account_fph)

    usable_payee_accounts = []
    for payee_account_fph in all_payee_accounts:
        if get_account_currency(payee_account_fph) == currency_fph:
            usable_payee_accounts.append(payee_account_fph)

    # The two lists now have to be passed to the template renderer:







# payment to an *account* -- select payer *account* ---------------------------
@app.route("/select_payer_account/<payee_account_fph>",
           methods = ["GET", "POST"])
@login_required
def select_payer_account_(payee_account_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "select_payer_account"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    # In contrast to the case of paying from an *account* (and therefore a
    # known *currency*), here a knowledge of the payee *account* tells us both
    # the *identity* and the *currency*. However, the payer *identity* may have
    # several accounts in this *currenccy*, so one of these must be selected.

    if payee_account_fph and re_fph.match(payee_account_fph):
        payee_account_fph, \
        payee_account_hrns, \
        etype, \
        m = identify_entity(payee_account_fph)
        if etype !=  "account":
            flash(payee_account_fph + " in URL slug is not an account")
            return redirect("/pay_to_account")
    else:
        flash("No payee account specified in URL slug")
        return redirect("/pay_to_account")

    payee_account_currency_fph, \
    payee_account_owner_fph, \
    payee_account_ahid_fph, \
    payee_account_balance, \
    payee_account_volume, \
    m = get_account_specific_properties(payee_account_fph)

    number_of_payer_accounts = 0
    payer_usable_accounts = []
    payer_accounts_list, m = list_agent_accounts(identity_fph)

    for account_fph in payer_accounts_list:

        account_currency_fph, \
        account_owner_fph, \
        account_ahid_fph, \
        account_balance, \
        account_volume, \
        m = get_account_specific_properties(account_fph)

#        print("account = " + account_fph + " > " + fph_to_hrns(account_fph))
#        print(
#            "currency = " + account_currency_fph + " > " \
#            + fph_to_hrns(account_currency_fph)
#        )

        if account_currency_fph == payee_account_currency_fph:
#            print(account_fph)
            a = {}
            a["fph"] = account_fph
            a["hrns"] = fph_to_hrns(account_fph)
            a["currency_fph"] = account_currency_fph
            a["balance"] = integer_to_money_format(account_balance)
            a["isneg"] = (account_balance < 0)
            payer_usable_accounts.append(a)
            number_of_payer_accounts += 1

    payer_has_accounts_available = (number_of_payer_accounts > 0)
#    print("payer_has_accounts_available = ", end = "")
#    print(payer_has_accounts_available)

    return render_template(
        "select_payer_account.html",
        title = "Select an account from which to pay",
        page = page,
        group = group,
        logged_in = logged_in,
        hub_mode = hub_mode,
        version = get_version(),
        payee_account_fph = payee_account_fph,
        payee_account_hrns = payee_account_hrns,
        specified_currency_fph = payee_account_currency_fph,
        specified_currency_hrns = fph_to_hrns(payee_account_currency_fph),
        number_of_payer_accounts = number_of_payer_accounts,
        payer_has_accounts_available = payer_has_accounts_available,
        payer_usable_accounts = payer_usable_accounts,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type
    )

# account details page --------------------------------------------------------
@app.route("/account_details/<account_fph>", methods = ["GET", "POST"])
@login_required
def account_details(account_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "account_details"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    # If an *account* has been specified (by FPH) in the URL slug
#    print("Account " + account_fph)

    account_fph, \
    account_hrns, \
    etype, \
    m = identify_entity(account_fph)

    if not account_fph:
        flash("The FPH in the URL cannot be identified.")
        return redirect("/account")
    elif etype !=  "account":
        flash("The FPH in the URL does not identify an account.")
        return redirect("/account")

    currency_fph, \
    owner_fph, \
    ahid_fph, \
    account_balance, \
    account_volume, \
    m = get_account_specific_properties(account_fph)
    if m:
        flash(m)
        return redirect("/account")

    account_balance_is_negative = account_balance < 0

    currency_fph, \
    currency_hrns, \
    currency_prefix, \
    currency_suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_specific_properties(currency_fph)


    #payments_history, m = dump_account_payments_csv(account_fph)
    payments_history, m = list_payments_for_account(account_fph)
    if m:
        flash(m)

    return render_template(
        "account_details.html",
        title = "Account details",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        account_fph = account_fph,
        account_hrns = account_hrns,
        account_balance = integer_to_money_format(account_balance),
        account_balance_is_negative = account_balance_is_negative,
        payments_history = payments_history,
        currency_prefix = currency_prefix,    # just added
        currency_suffix = currency_suffix,    # just added
        currency_fph = currency_fph,          # just added
        currency_hrns = currency_hrns         # just added
    )

# stewardships page ----------------------------------------------------------
@app.route("/stewardships/<identity_fph>")
@login_required
def stewardships(identity_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "stewardships"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
    group = "home" # Used to control top menu behaviour.

    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    stewardships, m = list_stewardships(primary_identity_fph)
    if m:
        splash(m)

    return render_template(
        "stewardships.html",
        title = "Stewardships",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        development_mode = development_mode,
        logged_in = logged_in,
        namespace_steward = namespace_steward,
        currency_steward = currency_steward
    )

# list stewardships -----------------------------------------------------------
@app.route("/stewardship/list/<primid_fph>", methods = ["GET", "POST"])
@login_required
def stewardships_list(primid_fph):

    return




# secids page -----------------------------------------------------------------
@app.route("/secids/<identity_fph>")
@login_required
def secids(identity_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "secids"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
    group = "home" # Used to control top menu behaviour.

    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    secids = list_secids(primary_identity_fph)

#    for secid_fph in secids:
#        print(secid_fph + " > " + fph_to_hrns(secid_fph))

    return render_template(
        "secids.html",
        title = "Secondary identities",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        development_mode = development_mode,
        logged_in = logged_in,
        namespace_steward = namespace_steward,
        secids = secids
    )




@app.route("/secid/manage/<secid_fph>", methods = ["GET", "POST"])
@login_required
def manage_secid(secid_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "secids"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
    group = "home" # Used to control top menu behaviour.

    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    secids = list_secids(primary_identity_fph)

#    for secid_fph in secids:
#        print(secid_fph + " > " + fph_to_hrns(secid_fph))

    return render_template(
        "manage_secid.html",
        title = "Manage an alias",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        development_mode = development_mode,
        logged_in = logged_in,
        namespace_steward = namespace_steward,
        secids = secids
    )






@app.route("/currency/<currency_fph>", methods = ["GET", "POST"])
@login_required
def currency(currency_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "currency"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_fph)
    if (etype != "currency"):
        return "", "", currency_fph + " is not a currency"

    currency_fph, \
    currency_hrns, \
    prefix, \
    suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_specific_properties(currency_fph)

    # Compile a list of the stewards of this *currency*, excluding the *primid*
    # of the *agent* logged in here:
    current_stewards = []
    for steward_fph in stewards_list:
        if steward_fph != primary_identity_fph:
            s = {}
            s["fph"] = steward_fph
            s["hrns"] = fph_to_hrns(steward_fph)
            current_stewards.append(s)

    form = StewardAddForm()



    return render_template(
        "currency.html",
        title = "Currency",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        form = form,
        currency_fph = currency_fph,
        currency_hrns = currency_hrns,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        current_stewards = current_stewards,
        development_mode = development_mode,
        logged_in = logged_in
    )


#
@app.route("/currency/steward/add/<currency_fph>", methods = ["GET", "POST"])
@login_required
def currency_steward_add(currency_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "currency_steward_add"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    currency_fph, \
    currency_hrns, \
    prefix, \
    suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_specific_properties(currency_fph)

    form = StewardAddForm()
    if form.validate_on_submit():
        new_steward_fph, \
        new_steward_hrns, \
        etype, \
        m = identify_entity(form.new_steward.data)
        if new_steward_fph:
            m = add_stewardship(currency_fph, new_steward_fph)
        else:
            flash(form.new_steward.data + " is not a registered identity")

        if hub_mode == "omtrad":
            return redirect("/home_ahc")
        else:
            return redirect("/home")

    return render_template(
        "currency_steward_add.html",
        title = "Add currency steward",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        form = form,
        currency_fph = currency_fph,
        currency_hrns = currency_hrns,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        stewards_list = stewards_list,
        logged_in = logged_in
    )

#
@app.route("/currency/steward/remove/<currency_fph>/<steward_fph>",
#           methods = ["GET", "POST"]
           methods = ["GET"]
          )
@login_required
def currency_steward_remove(currency_fph, steward_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "currency_steward_add"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    currency_fph, \
    currency_hrns, \
    prefix, \
    suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_specific_properties(currency_fph)

    #stewards_fph_list, m = list_stewards(currency_fph)
    #    primary_identity_fph)
    if primary_identity_fph in stewards_list:
        m = remove_steward(currency_fph, primary_identity_fph, steward_fph)

    if hub_mode == "omtrad":
        return redirect("/home_ahc")
    else:
        return redirect("/home")

# MANAGEMENT ==================================================================

# management ------------------------------------------------------------------
@app.route("/manage", methods = ["GET", "POST"])
@login_required
def manage():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "manage"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
    group = "management" # Used to control top menu behaviour.

    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    return render_template(
        "manage.html",
        title = "Manage your SLATE settings",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        development_mode = development_mode,
        namespace_steward = namespace_steward,
        currency_steward = currency_steward
    )


# create a currency -----------------------------------------------------------
@app.route("/create_currency", methods = ["GET", "POST"])
@login_required
def create_currency():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "create_currency"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = True
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    form = CurrencyCreateForm()
    if form.validate_on_submit():
        namespace_fph, \
        namespace_hrns, \
        etype, \
        m = identify_entity(form.namespace_id.data.strip().lstrip("."))
        if m:
            flash(m)
            return redirect("/create_currency")
        if not namespace_fph:
            flash("Parent namespace does not exist")
            return redirect("/create_currency")

        currency_name = form.currency_name.data
        # Check whether an entity with the proposed HRNS exists already.
        proposed_hrns = currency_name + "." + namespace_hrns
        if hrns_exists_already(proposed_hrns):
            flash(proposed_hrns + " is already registered")
            return redirect("/create_currency")

        currency_fph, \
        currency_hrns,\
        m = new_currency(
                currency_name,
                namespace_fph,
                primary_identity_fph,
                form.prefix_symbol.data,
                form.suffix_symbol.data,
                form.default_account_name.data
            )
        flash(
            "A new currency has been created, identified as \n" \
            + currency_hrns
#            + currency_hrns + " [" + currency_fph + "]"
        )

        if hub_mode == "omtrad":
            return redirect("/home_ahc")
        else:
            return redirect("/home")

    return render_template(
        "create_currency.html",
        title = "Create a currency",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        form = form,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        development_mode = development_mode,
        namespace_steward = namespace_steward,
        currency_steward = currency_steward
    )

# create an *ahid*-*currency* pairing -----------------------------------------
#@app.route("/create_ahid/<owner_fph>", methods = ["GET", "POST"])
@app.route("/create_pairing/<owner_fph>", methods = ["GET", "POST"])
@login_required
def create_pairing(owner_fph = ""):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    if hub_mode != "omtrad":
        flash("Invalid opertional mode for this endpoint")
        return redirect("/home")

    page = "create_pairing"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = True
    logged_in = current_user.is_authenticated

    if owner_fph:
        owner_fph, \
        owner_hrns, \
        owner_type, \
        m = identify_entity(owner_fph)
        if m:
            flash(m)
            return redirect("/home")
        if owner_fph == "":
            flash("The owner FPH in the URL cannot be identified")
            return redirect("/home")

    if hub_mode != "omtrad":
        flash("This endpoint is not valid in the current mode.")
        return redirect("/home")

    primid_fph, \
    primid_hrns, \
    primid_type, \
    m = identify_entity(current_user.get_id())

    # In omtrad mode the *working identity* is always the *primary identity*.
    working_identity_fph = primid_fph
    working_identity_hrns = primid_hrns
    working_identity_type = primid_type

    form = PairingCreateForm()

    if form.validate_on_submit():

        ahid_hrns = form.ahid_hrns.data
        if not re_hrns.match(ahid_hrns):
            flash(ahid_hrns + " is not a valid identifier string")
            return redirect("/create_pairing/" + owner_fph)
            #return redirect("/create_ahid/" + owner_fph)
        if not is_in_private_namespace(ahid_hrns, owner_hrns):
        #if not is_ancestor(ahid_hrns, owner_hrns):
            flash(ahid_hrns + " is not in private namespace of " + owner_hrns)
            return redirect("/create_pairing/" + owner_fph)
            #return redirect("/create_ahid/" + owner_fph)

        currency_id = form.currency_id.data

        currency_fph, \
        currency_hrns, \
        etype, \
        m = identify_entity(currency_id)
        if m:
            flash(m)
            return redirect("/home")
        if etype !=  "currency":
            flash(currency_id + " is not a currency")
            #return redirect("/home")
            return redirect("/create_pairing/" + owner_fph)
            #return redirect("/create_ahid/" + owner_fph)

        currency_fph, \
        currency_hrns, \
        prefix, \
        suffix, \
        default_account_name, \
        stewards_list, \
        m = get_currency_specific_properties(currency_fph)

        account_fph = create_new_pairing(
                          working_identity_fph,
                          ahid_hrns,
                          currency_hrns
                      )

        if hub_mode == "omtrad":
            return redirect("/home_ahc")
        else:
            return redirect("/home")

    return render_template(
        "create_ahid_currency_pair.html",
        title = "Pair an account-holder with a currency",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        form = form,
        primary_identity_type = "login identity",
        primary_identity_fph = primid_fph,
        primary_identity_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        development_mode = development_mode,
        namespace_steward = namespace_steward
    )



# create an *account* ---------------------------------------------------------
@app.route("/create_account/<owner_fph>", methods = ["GET", "POST"])
@login_required
def create_account(owner_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "create_account"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = True
    logged_in = current_user.is_authenticated

    owner_fph, \
    owner_hrns, \
    owner_type, \
    m = identify_entity(owner_fph)
    if m:
        flash(m)
        return redirect("/home")
    if owner_fph == "":
        flash("The owner FPH in the URL cannot be identified")
        return redirect("/home")

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    if hub_mode == "slate_minimal":
        form = AccountCreateFormMinimal()
    else:
        form = AccountCreateForm()

    if form.validate_on_submit():

        currency_id = form.currency_id.data

        currency_fph, \
        currency_hrns, \
        etype, \
        m = identify_entity(currency_id)
        if m:
            flash(m)
            #return redirect("/create_account")
            return redirect("/home")
        if etype !=  "currency":
            flash(currency_id + " is not a currency")
            return redirect("/home")

        # 2025-03-13:
        # If mode = "slate_minimal", the *identity* is always a *primid* and
        # can have no more than one *account* in any *currency*:
        #
#        accounts_fph_list, m = list_primid_accounts(primary_identity_fph)
        accounts_fph_list, m = list_agent_accounts(primary_identity_fph)
#        for account_fph in accounts_fph_list:
#            account_currency_fph = get_account_currency(account_fph)
#            if account_currency_fph == currency_fph:
#                flash("You are already using currency " + currency_hrns)
#                return redirect("/home")


        if hub_mode != "slate_minimal":
            namespace_fph, \
            namespace_hrns, \
            etype, \
            m = identify_entity(form.namespace_id.data.strip().lstrip("."))
            if m:
                flash(m)
                return redirect("/home")
            if not namespace_fph:
                flash("Parent namespace does not exist")
                return redirect("/home")

            account_name = form.account_name.data
            # Check whether an entity with the proposed HRNS exists already.
            proposed_hrns = account_name + "." + namespace_hrns
            if hrns_exists_already(proposed_hrns):
                flash(proposed_hrns + " is already registered")
                return redirect("/home")

        else:
            # 2025-03-13:
            # Temporary fudge for automatic account naming:
            #n = primary_identity_hrns.split(".")

            #account_name = primary_identity_hrns + "." + currency_hrns
            #namespace_fph = hrns_to_fph("cc")
            # Since this account name is hidden, it can be safely constructed
            # from a concatentation of *primid* and *currency* HRNS and placed
            # in the "cc" seed *namespace*.

            currency_fph, \
            currency_hrns, \
            prefix, \
            suffix, \
            default_account_name, \
            stewards_list, \
            m = get_currency_specific_properties(currency_fph)

            account_name = default_account_name
            namespace_fph = primary_identity_fph



        account_fph, \
        account_hrns, \
        m = new_account(
                account_name,
                namespace_fph,
                "", # *ahid_fph* not required here
                owner_fph, # the owner of this *account*
                currency_fph
            )
        if m:
            flash(m)
        if hub_mode != "slate_minimal":
            flash("A new account " + account_hrns + " has been created")
        return redirect("/home")









    return render_template(
        "create_account.html",
        title = "Create an account",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        form = form,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        development_mode = development_mode,
        namespace_steward = namespace_steward
    )

# list *secondary identities* =================================================
@app.route("/identity/list", methods = ["GET", "POST"])
@login_required
def list_identiies():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "list_identities"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = "login identity"
    working_identity_type = etype_to_adtype(working_identity_type)

    secids_fph_list = list_secids(primary_identity_fph)
    identities = []
    s = {}
    s["fph"] = primary_identity_fph
    s["hrns"] = primary_identity_hrns
    identities.append(s)
    for secid_fph in secids_fph_list:
        s = {}
        s["fph"] = secid_fph
        s["hrns"] = fph_to_hrns(secid_fph)
        identities.append(s)

    return render_template(
        "list_identities.html",
        title = "List identities",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        #secids_list = secids_list
        identities = identities
    )

# create *secondary identity* =================================================
@app.route("/create_secid", methods = ["GET", "POST"])
@login_required
def create_secid():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    group = "home" # Used to control top menu behaviour.
    page = "create_secid"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    form = SecidCreateForm()
    if form.validate_on_submit():
        parent_namespace_fph, \
        parent_namespace_hrns, \
        parent_namespace_type, \
        m = identify_entity(form.parent_namespace_id.data.strip().lstrip("."))
        if m:
            flash(m)
            return redirect("/create_secid")
        if not parent_namespace_fph:
            flash("Parent namespace does not exist")
            return redirect("/create_secid")
        # The *namespace* may actually be a *primid* or *secid* (serving as the
        # root private *namespace*) in which case a default

        secid_name = form.secid_name.data
        # Check whether an entity with the proposed HRNS exists already.
        proposed_hrns = secid_name + "." + parent_namespace_hrns
        if hrns_exists_already(proposed_hrns):
            flash(proposed_hrns + " is already registered")
            return redirect("/create_secid")

        secid_fph, \
        secid_hrns, \
        m = new_secid(
                secid_name,
                parent_namespace_fph,
                primary_identity_fph # the *primd* of this *secid*
            )
        flash(
            "A new alias has been created, identified as \n" \
            + secid_hrns
#            + secid_hrns + " [" + secid_fph + "]"
        )

        # An *account* is now created for this new *alias* in the default
        # *currency* of the parent *namespace*:

        default_currency_fph = get_default_currency(parent_namespace_fph)
        m = set_default_currency(secid_fph, default_currency_fph)
        if m:
            flash(m)
            return redirect("/create_secid")

        currency_fph, \
        currency_hrns, \
        prefix, \
        suffix, \
        default_account_name, \
        stewards_list, \
        m = get_currency_specific_properties(default_currency_fph)

        account_fph, \
        account_hrns, \
        m = new_account(
            default_account_name,
            secid_fph,
            secid_fph,
            "", # *ahid_fph* not required here
            default_currency_fph
        )
        flash(
            "Account " + account_hrns + " has been created for " \
            + secid_hrns + " in currency " + currency_hrns
        )

        # The new *alias* also serves as a (private) *namespace* so must be
        # assigned a default *currency*. No other information being available
        # at this point, the default *currency* of the parent *namespace* is
        # used as the initial default *currency* of the *alias-namespace*.

        return redirect("/home")

    return render_template(
        "create_secid.html",
        title = "Create an alias",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        form = form,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type
    )

# create a new namespace ------------------------------------------------------
@app.route("/create_namespace", methods = ["GET", "POST"])
@login_required
def create_namespace():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "create_namespace"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = True
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    form = NamespaceCreateForm()
    if form.validate_on_submit():
        parent_namespace_fph, \
        parent_namespace_hrns, \
        etype, \
        m = identify_entity(form.parent_namespace_id.data.strip().lstrip("."))
#        if m:
#            flash(m)
#            return redirect("/create_namespace")
        if not parent_namespace_fph:
            flash("Parent namespace does not exist")
            return redirect("/create_namespace")

        inh_default_currency_fph = get_default_currency(parent_namespace_fph)
#        print(
#            "inherited default currency = " \
#            + fph_to_hrns(inh_default_currency_fph)
#        )

        default_currency_fph, \
        default_currency_hrns, \
        etype, \
        m = identify_entity(form.default_currency_id.data.strip().lstrip("."))
        if default_currency_fph == "":
            default_currency_fph = inh_default_currency_fph
            default_currency_hrns = fph_to_hrns(default_currency_fph)


        namespace_name = form.namespace_name.data
        # Check whether an entity with the proposed HRNS exists already.
        proposed_hrns = namespace_name + "." + parent_namespace_hrns
        if hrns_exists_already(proposed_hrns):
            flash(proposed_hrns + " is already registered")
            return redirect("/create_namespace")

        namespace_fph, \
        namespace_hrns,\
        m = new_namespace(
                namespace_name,
                parent_namespace_fph,
                default_currency_fph,
                primary_identity_fph
            )
        flash(
            "A new namespace has been created, identified as \n" \
            + namespace_hrns
#            + namespace_hrns + " [" + namespace_fph + "]"
        )
        return redirect("/home")

    return render_template(
        "create_namespace.html",
        title = "Create a namespace",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        form = form,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type
    )

# list the existing namespaces ------------------------------------------------
@app.route("/list_namespaces", methods = ["GET", "POST"])
@login_required
def list_namespaces():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "list_namespaces"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    active_namespaces, m = list_all_namespaces()
    if m:
        flash(m)
    available_namespaces = []
    for namespace in active_namespaces:
        n = {}
        n["fph"] = namespace
        n["hrns"] = fph_to_hrns(namespace)
        available_namespaces.append(n)

    return render_template(
        "list_namespaces.html",
        title = "List available namespaces",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        available_namespaces = available_namespaces
    )

# add steward to entitity =====================================================
@app.route("/steward/add/<entity_fph>", methods = ["GET", "POST"])
@login_required
def add_steward():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "add_steward"
    previous_page = session["previous_page"]
    session["previous_page"] = page
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    # The entity (*namespace* or *currency* to which this new steward is to be
    # added):

    entity_fph, \
    entity_hrns, \
    etype, \
    m = identify_entity(entity_fph) # from URL slug
    if m:
        flash(m)
        return redirect("/home")
    if entity_fph == "":
        flash("The entity specified does not exist")
        return redirect("/home")
    if etype == "namespace":
        namespace_exists, \
        namespace_private, \
        namespace_active,
        stewards_list, \
        m = namespace_status(namespace_fph)
    elif etype == "currency":
        currency_fph, \
        currency_hrns, \
        prefix, \
        suffix, \
        default_account_name, \
        stewards_list, \
        m = get_currency_specific_properties(currency_fph)
    else:
        flash("The entity specified is not of a stewarded type")
        return redirect("/home")

    form = StewardAddForm()
    if form.validate_on_submit():
        steward_fph, \
        steward_hrns, \
        etype, \
        m = identify_entity(form.new_steward.data)
        if m:
            flash(m)
            return redirect("/currency/" + currency_fph)
        if etype == "primid":
            stewards_list.append(primary_identity_fph)
            with sqlite3.connect(ENTITIES_DB) as conn:
                cursor = conn.cursor()
                if etype == "namespace":
                    cursor.execute(
                        """
                        UPDATE namespaces
                        SET stewards_fph_list = ?
                        WHERE entity_fph = ?
                        """,
                        (pickle.dumps(stewards_list), namespace_fph)
                    )
                elif etype == "currency":
                    cursor.execute(
                        """
                        UPDATE currencies
                        SET stewards_fph_list = ?
                        WHERE entity_fph = ?
                        """,
                        (pickle.dumps(stewards_list), currency_fph)
                    )
                conn.commit()
                cursor.close()
        else:
            flash("The steward must be the primary identity of an agent")
            return redirect("/currency/" + currency_fph)
    return

#==============================================================================
#
@app.route("/export/<path:file>")
@login_required
def export(file):
    exports = os.path.join(app.root_path, "export", file)
    return send_file(exports, as_attachment=True)

#------------------------------------------------------------------------------
# Export *account* jourbal:
@app.route("/account/export/<account_fph>", methods = ["GET", "POST"])
@login_required
def export_account_csv(account_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()

    page = "export_account"
    previous_page = session["previous_page"]
    session["previous_page"] = page
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if hub_mode == "omtrad":
        working_identity_fph = primary_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    elif "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    account_fph, \
    account_hrns, \
    etype, \
    m = identify_entity(account_fph) # from URL slug
    if m:
        flash(m)
        return redirect("/home")
    if account_fph == "":
        flash("The entity specified does not exist")
        return redirect("/home")
    if etype != "account":
        flash("The entity specified is not an account")
        return redirect("/home")

    currency_fph, \
    owner_fph, \
    ahid_fph, \
    balance, \
    volume, \
    m = get_account_specific_properties(account_fph)
    if m:
        flash(m)
        return redirect("/home")
    ahid_hrns = fph_to_hrns(ahid_fph)

#    print()
#    print("currency_fph: " + currency_fph)
#    print("owner_fph: " + owner_fph)
#    print("ahid_fph: " + ahid_fph)
#    print("balance: " + str(balance))
#    print("volume: " + str(volume))
#    print("account: " + account_fph + " > " + account_hrns)
#    print("ahid: " + ahid_fph + " > " + ahid_hrns)

    owner_fph, \
    owner_hrns, \
    etype, \
    m = identify_entity(owner_fph)
    if m:
        flash(m)
        return redirect("/home")
    if etype == "secid":
        owner_primid_fph, m = get_primid(owner_fph)
    else:
        owner_primid_fph =  primary_identity_fph
    # This may appear a little convoluted, but simplifying it is not an urgent
    # priority.
    if owner_primid_fph != primary_identity_fph:
        flash("None of your identities owns this account")
        return redirect("/home")

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_fph)
    if m:
        flash(m)
        return redirect("/home")
    if etype !=  "currency":
        flash(currency_id + " is not a currency")
        return redirect("/home")

    csv_file, \
    m = dump_account_payments_csv(account_fph, True)
    if m:
        flash(m)
        return redirect("/home")

    return render_template(
        "export_account_journal.html",
        title = "export_account_journal",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        currency_fph = currency_fph,
        currency_hrns = currency_hrns,
        account_fph = account_fph,
        account_hrns = account_hrns,
        #csv_export_path = csv_export_path,
        ahid_fph = ahid_fph,
        ahid_hrns = ahid_hrns,
        csv_file = csv_file
    )

#------------------------------------------------------------------------------
# Export *currency* journal:
@app.route("/currency/export/<currency_fph>", methods = ["GET", "POST"])
@login_required
def export_currency_csv(currency_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "export_currency"
    previous_page = session["previous_page"]
    session["previous_page"] = page
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if hub_mode == "omtrad":
        working_identity_fph = primary_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    elif "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    currency_fph, \
    currency_hrns, \
    etype, \
    m = identify_entity(currency_fph) # from URL slug
    if m:
        flash(m)
        return redirect("/home")
    if currency_fph == "":
        flash("The entity specified does not exist")
        return redirect("/home")
    if etype != "currency":
        flash("The entity specified is not a currency")
        return redirect("/home")

    currency_fph, \
    currency_hrns, \
    prefix, \
    suffix, \
    default_account_name, \
    stewards_list, \
    m = get_currency_specific_properties(currency_fph)
    if m:
        flash(m)
        return redirect("/home")

    if not (primary_identity_fph in stewards_list):
        flash("You are not a steward of this currency")
        return redirect("/home")

    csv_file, \
    m = dump_currency_payments_csv(currency_fph, False)
    if m:
        flash(m)
        return redirect("/home")

    return render_template(
        "export_currency_journal.html",
        title = "export_currency_journal",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        currency_fph = currency_fph,
        currency_hrns = currency_hrns,
        #csv_export_path = csv_export_path
        csv_file = csv_file
    )



#==============================================================================
# CSV import: sandbox payments set ============================================
#
# The screen is use to import a set of payments for sandbox purposes (as CSV),
# each row having the format:
#   payer_account:payee_account:amount:annotation
# The form used to import the CSV file provides fields for
# - the *namespace* in which any new *accounts* will all be created
# - the *currency* of these accounts
# Any *accounts* not already registered are created on the fly in the
# *namespace* specified.
# All *accounts* listed in the file belong to the agent importing it.


@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        filename = random_filename()
        file.save(SLATE_TEMP + "/" + filename)
        flash("CSV dataset imported")
        return redirect("/import/dataset/" + filename)
    else:
        flash("CSV dataset could not be imported")
        return redirect("/import/dataset")



#@app.route(
#    "/importing/<file>", defaults={"file": None}, methods=["GET", "POST"]
#)
@app.route(
    "/importing/<file>", methods=["GET", "POST"]
)
def importing(file):
    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    if hub_mode != "omtrad":
        flash("You are working in the wrong mode to use this import function")
        return redirect("/home_ahc")
    page = "dataset_import"
    previous_page = session["previous_page"]
    session["previous_page"] = page
    group = "home" # Used to control top menu behaviour.
    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())
    working_identity_fph = primary_identity_fph
    working_identity_hrns = primary_identity_hrns
    session["working_identity"] = working_identity_fph
    logged_in = current_user.is_authenticated
    print(file)
    if file:
        print("\nGroucho")
        tfpath = SLATE_TEMP + "/" + file
        if os.path.exists(tfpath):
            print("Chico")
            flash("Please wait while the CSV file is being processed ...")
            report, errors = import_csv_dataset(tfpath, primary_identity_fph)
            if len(errors) > 0:
                for line in errors:
                    flash(line)
            os.unlink(tfpath)
            flash("Processing completed")
        return redirect("/home_ahc")
    else:
        return redirect("/home_ahc")
    return render_template(
        "dataset_importing.html",
        title = "Processing import of CSV payment set",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        logged_in = logged_in,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns
    )

#@app.route("/import/dataset/<filename>", methods = ["GET", "POST"])
@app.route("/import/dataset", methods = ["GET", "POST"])
@login_required
def import_payment_set():
    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    if hub_mode != "omtrad":
        flash("You are working in the wrong mode to use this import function")
        return redirect("/home_ahc")
    page = "dataset_import"
    previous_page = session["previous_page"]
    session["previous_page"] = page
    group = "home" # Used to control top menu behaviour.
    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())
    working_identity_fph = primary_identity_fph
    working_identity_hrns = primary_identity_hrns
    session["working_identity"] = working_identity_fph
    logged_in = current_user.is_authenticated

    if request.method == 'POST':
        if "csv_file" in request.files:
            file = request.files["csv_file"]
            filename = random_filename()
            tfpath = SLATE_TEMP + "/" + filename
            file.save(tfpath)
            with open(IMPORT_QUEUE, "a") as iqf:
                iqf.write(primary_identity_fph + ":" + filename + "\n")
            flash("The CSV file has been added to the import queue.")
            return redirect("/home_ahc")
        else:
            flash("No file uploaded")
            return redirect("/dataset/import")

    return render_template(
        "dataset_import.html",
        title = "Import CSV payment set",
        form = CSVImportForm(),
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        logged_in = logged_in,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns
    )


#==============================================================================















@app.route("/import/create/namespaces", methods = ["GET", "POST"])
@login_required
def upload_create_namespaces():

    # Display link to file upload dialogue

    # Upload CSV file containing instructions to create a set of *namespaces*
    # from the following fields:
    # - name
    # - parent *namespace*
    # - initial steward (an existing *identity*)
    # - default *currency* for new registrations in this *namespace*

    # Parse the CSV file to create the *namespaces*

    return

#
@app.route("/import/create/identities", methods = ["GET", "POST"])
@login_required
def upload_create_identities():

    # Display link to file upload dialogue

    # Upload CSV file containing instructions to create a set of *login
    # identities* from the following fields:
    # - name
    # - parent *namespace*
    # - *currency* for the initial *account*
    # - password (optional)  [auto-generated if none provided]
    # - PIN (optional)  [auto-generated if none provided]
    # - email address (required for access recovery purposes)

    # Parse the CSV file to create the *login identtiies*

    # Make a summary of the *login identities* created available (CSV) for
    # immediate download (required because some password and PIN may have been
    # auto-generated).

    return

#
@app.route("/import/create/currencies", methods = ["GET", "POST"])
@login_required
def upload_create_currencies():

    # Display link to file upload dialogue

    # Upload CSV file containing instructions to create a set of *currencies*
    # from the following fields:
    # - name
    # - parent *namespace*
    # - initial steward (an existing *identity*)
    # - default name for new *accounts* created in this *currency*
    # - a display prefix (optional)
    # - a display suffix (optional)

    # Parse the CSV file to create the *currencies*



    return

#
@app.route("/import/create/accounts", methods = ["GET", "POST"])
@login_required
def upload_create_accounts():

    # Display link to file upload dialogue

    # Upload CSV file containing instructions to create a set of *accounts*.
    # Each *account* pairs an *identity* with a *currency*, so the following
    # fields are needed:
    # - name
    # - parent *namespace*
    # - *currency*
    # - *identity* (of the *accounts*'s owner)

    # Parse the CSV file to create the *accounts*

    return

#
@app.route("/import/create/payments", methods = ["GET", "POST"])
@login_required
def import_create_payments():

    # Display link to file upload dialogue

    # Upload CSV file containing instructions to create a set of *payments*.
    #
    # Both payer and payee *accounts* can be identified either by *account*
    # identifier or by *identity*+*currency*, so the following fields are
    # needed:
    # - *currency* (only if neither payer *account* nor payee *account* given)
    # - payer *account* (only if *currency* and payer *identity* not specified)
    # - payer *identity* (only if payer *account* not specified)
    # - payee *account* (only if *currency* and payee *identity* not specified)
    # - payee *identity* (only if payee *account* not specified)
    #
    # The payments may be specified by different combinations of fields,
    # following precedence rules and checked for consistency.

    # Parse the CSV file to create the set of *payments*

    return


# messaging ===================================================================

@app.route("/message/list", methods = ["GET", "POST"])
@login_required
def messages():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "messages"
    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
        previous_page = "home"
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    hub_mode = get_hub_mode()
    #version = get_version()()
 ### New variable added

    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    # List all identities:
    identity_list = []
    identity_list.append(primary_identity_fph)
    secids_list = list_secids(primary_identity_fph)
    for secid_fph in secids_list:
        identity_list.append(secid_fph)

#    print("Indentities listed:")
#    for identity_fph in identity_list:
#        print("\t" + fph_to_hrns(identity_fph))

    total_number_of_messages = 0
    total_number_of_indelible_messages = 0
    # List identities for which messages are available:
    message_recipients_list = [] # (list of dictionaries for template)
    for identity_fph in identity_list:
        number_of_messages, \
        number_of_indelible_messages = messages_available(identity_fph)

#        print("number_of_messages = " + str(number_of_messages))
#        print(
#            "number_of_indelible_messages = " \
#            + str(number_of_indelible_messages)
#        )
        total_number_of_messages += number_of_messages
        total_number_of_indelible_messages += number_of_indelible_messages

        if number_of_messages > 0:
            m = {}
            m["fph"] = identity_fph
            m["hrns"] = fph_to_hrns(identity_fph)
            if identity_fph == primary_identity_fph: # extend later
                m["primid"] = True
            else:
                m["primid"] = False
            if number_of_indelible_messages > 0:
                m["some_indelible"] = True
            else:
                m["some_indelible"] = False

#            print(m)
            message_recipients_list.append(m)

    if total_number_of_messages > 0:
        number_of_messages = str(total_number_of_messages)
    else:
        number_of_messages = ""
    if total_number_of_indelible_messages > 0:
        number_of_indelible_messages = str(total_number_of_indelible_messages)
    else:
        number_of_indelible_messages = ""

    return render_template(
        "messages_list.html",
        title = "Messages",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        logged_in = logged_in,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        message_recipients_list = message_recipients_list,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
    )



@app.route("/message/send", methods = ["GET", "POST"])
@login_required
def message_send():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "send_message"
    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
        previous_page = "home"
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    hub_mode = get_hub_mode()
    #version = get_version()()
 ### New variable added

    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)

    form = UserMessageForm()
    if form.validate_on_submit():

        recipient_fph, \
        recipient_hrns, \
        recipient_type, \
        m = identify_entity(form.recipient.data)
        if m:
            flash(m)
            return redirect("/home")
        if recipient_fph == "":
            flash("Recipient cannot be identified")
            return redirect("/home")

        if not (recipient_type in ["primid", "secid", "currency"]):
            flash("Invalid recipient type")
            return redirect("/home")

        if recipient_type == "currency":
            if form.broadcast.data:
                #broadcast_to_currency_users(recipient_fph)
                flash("broadcast_to_currency_users( )  not yet implemented")
                return redirect("/home")
            else:
                flash("Cannot broadcast to currency users if box unticked")
                return redirect("/home")

        now = datetime.now()
        message_timestamp = now.strftime("%Y-%m-%d_%H:%M:%S")
#        print("message_timestamp = ", end="")
#        print(message_timestamp)
#        print("now = ", end="")
#        print(now)
#        today = date.now()
#        print("today = ", end="")
#        print(today)

#        date_time = now.strftime("%Y-%m-%d_%H:%M:%S")
        date_today = now.strftime("%Y%m%d")

        category = form.category.data
#        print("category = ", end="")
#        print(category)

        subject = form.subject.data

        #expiry_datetime = form.expiry_date.data + "_00:00:00"
        #expiry_datetime = form.expiry_datetime.data
        expiry_date = form.expiry_date.data
#        print("expiry_date = ", end="")
#        print(expiry_date)
        expiry_date_ = expiry_date.strftime("%Y%m%d")
#        print("expiry_date_ = ", end="")
#        print(expiry_date_)
        expiry_datetime = expiry_date.strftime("%Y-%m-%d_%H:%M:%S")




        #if expiry_datetime < now:
        if expiry_date_ < date_today:
            flash("The expiry date cannot be in the past.")

        lifespan = form.lifespan.data
        longevity = lifespan + unixtime_int()
        #unixtime = unixtime_int()

        message_body = form.message_body.data


#        print("To: " + recipient_hrns)
#        print("Category: " + category)
#        print("Subject: " + subject)
#        print("Expiry date: ", end="")
#        print(expiry_date)
#        print("Message body: " + message_body)

        em = send_message(
                message_timestamp,
                working_identity_fph,   # FPH or HRNS
                recipient_fph,          # FPH or HRNS
                category,               # string
                "",                     # string
                subject,                # string
                "",
                longevity,              # integer: lifespan (seconds)
                expiry_datetime,        # string: YYYY-MM-DD_hh:mm:ss
                "",                     # string
                "",                     # string
                "",                     # integer
                message_body,           # string
                False                   # boolean
            )
        if em:
            flash(em)
            return redirect("/home")
        else:
            return redirect("/message/list")


    return render_template(
        "message_send.html",
        title = "Send user message",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        logged_in = logged_in,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        form = form
    )







@app.route("/message/show/<recipient_fph>", methods = ["GET", "POST"])
@login_required
def messages_show(recipient_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "show_messages"
    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
        previous_page = "home"
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    hub_mode = get_hub_mode()
    #version = get_version()()
 ### New variable added

    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    primary_identity_fph, \
    primary_identity_hrns, \
    primary_identity_type, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, \
        working_identity_hrns, \
        working_identity_type, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primary_identity_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primary_identity_hrns
        working_identity_type = primary_identity_type
    working_identity_type = etype_to_adtype(working_identity_type)


    # NB, this bit has been duplicated from "/home" so should be moved into a
    # function in app/core/messaging.py
    #
    # List all identities:
    identity_list = []
    identity_list.append(primary_identity_fph)
    secids_list = list_secids(primary_identity_fph)
    for secid_fph in secids_list:
        identity_list.append(secid_fph)
    total_number_of_messages = 0
    total_number_of_indelible_messages = 0
    # List identities for which messages are available:
    message_recipients_list = [] # (list of dictionaries for template)
    for identity_fph in identity_list:
        number_of_messages, \
        number_of_indelible_messages = messages_available(identity_fph)
        total_number_of_messages += number_of_messages
        total_number_of_indelible_messages += number_of_indelible_messages
    if total_number_of_messages > 0:
        number_of_messages = str(total_number_of_messages)
    else:
        number_of_messages = ""
    if total_number_of_indelible_messages > 0:
        number_of_indelible_messages = str(total_number_of_indelible_messages)
    else:
        number_of_indelible_messages = ""

    recipient_fph, \
    recipient_hrns, \
    etype, \
    m = identify_entity(recipient_fph)
    if not (etype in ["primid", "secid"]):
        flash("Recipient is not an agent")
        return redirect("/home")

    message_list = fetch_messages(recipient_fph)
    any_messages = len(message_list) > 0

    return render_template(
        "messages_show.html",
        title = "Messages",
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        logged_in = logged_in,
        primary_identity_type = "login identity",
        primary_identity_fph = primary_identity_fph,
        primary_identity_hrns = primary_identity_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        recipient_hrns = recipient_hrns,
        any_messages = any_messages,
        message_list = message_list,
        number_of_indelible_messages = number_of_indelible_messages,
        number_of_messages = number_of_messages
    )


# Delete a single message:
#
@app.route("/message/delete/<recipient_fph>/<message_id>",
           methods = ["GET", "POST"])
@login_required
def message_delete(recipient_fph, message_id):

    primid_fph, \
    primid_hrns, \
    primid_type, \
    m = identify_entity(current_user.get_id())

    recipient_fph, \
    recipient_hrns, \
    recipient_type, \
    m = identify_entity(recipient_fph)

    if recipient_fph == "":
        flash("ERROR: recipient is unregistered")
        return redirect("/home")

    if (recipient_type == "primid") and (recipient_fph != primid_fph):
        flash("ERROR: recipient is incorrect primid")
        return redirect("/home")

    if (recipient_type == "secid"):
        secids_list = list_secids(primid_fph)
        if not (recipient_fph in secids_list):
            flash("ERROR: recipient secid does not belong to current primid")
            return redirect("/home")

    if not isinstance(message_id, str):
        flash("ERROR: invalid message ID in URL")
        return redirect("/home")

    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
        previous_page = "home"

    em = delete_message(message_id)
    if em:
        flash(em)

    return redirect("/message/show/" + recipient_fph)







# help ========================================================================
@app.route("/help")
def help():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    #version = get_version()()


    page = "help"
    group = ""
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated
    return render_template(
        "help.html",
        title = "help",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = hub_mode,
        version = get_version(),
        development_mode = development_mode,
        namespace_steward = namespace_steward,
        currency_steward = currency_steward
    )
