import os
import json
from pathlib import Path
import sys
import pickle
import sqlite3

import bcrypt
from itsdangerous import URLSafeTimedSerializer

from datetime import datetime, date

import urllib.parse

## SLATE components: -----------------------------------------------------------

from app.core.constants import NSS
from app.core.constants import PAYMENTS_DB
from app.core.constants import SLATE_TEMP, IMPORT_QUEUE, IMPORTING
from app.core.constants import QR_CODES

#from app.core.constants import SLATE_EXPORT, SLATE_IMPORT

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.fph_hrns_maps import hrns_exists_already

from app.core.common import unixtime_int

from app.core.slate_core import get_entity_types
from app.core.slate_core import get_account_currency
from app.core.slate_core import identify_entity
from app.core.slate_core import entity_type_is_registered
from app.core.slate_core import entity_types_are_registered
from app.core.slate_core import new_primid
from app.core.slate_core import update_primid_access_details
from app.core.slate_core import new_namespace
from app.core.slate_core import new_currency
from app.core.slate_core import new_account
from app.core.slate_core import account_status
#from app.core.slate_core import entity_is_active
from app.core.slate_core import list_namespace_stewardships
from app.core.slate_core import list_currency_stewardships
#from app.core.slate_core import list_namespace_stewards
#from app.core.slate_core import list_currency_stewards
from app.core.slate_core import list_stewards
from app.core.slate_core import retrieve_primid_access_details
from app.core.slate_core import list_agent_accounts
from app.core.slate_core import list_ahids
from app.core.slate_core import get_namespace_properties
from app.core.slate_core import get_currency_properties
from app.core.slate_core import get_account_properties
from app.core.slate_core import set_default_currency
from app.core.slate_core import get_default_currency
from app.core.slate_core import list_all_namespaces
from app.core.slate_core import hrns_to_name_and_namespace
from app.core.slate_core import authenticate_primid_email
from app.core.slate_core import get_hub_mode
from app.core.slate_core import get_version
#from app.core.slate_core import add_stewardship, remove_steward
from app.core.slate_core import add_currency_stewardship
from app.core.slate_core import add_namespace_stewardship
from app.core.slate_core import remove_currency_stewardship
#from app.core.slate_core import remove_namespace_stewardship
from app.core.slate_core import random_filename
#from app.core.slate_core import get_config

from app.core.configdb import get_config
from app.core.qrcode import qrencode_invitation

from app.core.slate_core import retrieve_pmap
from app.core.slate_core import new_pairing
from app.core.slate_core import retrieve_pairing_account_fph
#from app.core.slate_core import ah_payment
from app.core.payments import ah_payment
#from app.core.slate_core import import_csv_dataset
from app.core.slate_core import is_ancestor, is_in_private_namespace
from app.core.slate_core import get_ahid_primid

from app.core.csv_import_dataset import import_csv_dataset

from app.core.slate_session import create_slate_session_db
from app.core.slate_session import session_save_currencies_available
from app.core.slate_session import session_retrieve_currencies_available
from app.core.slate_session import session_save_payment_options
from app.core.slate_session import session_retrieve_payment_options
from app.core.slate_session import remove_slate_session_data

from app.core.regexp_list import re_fph, re_hrns, re_email
from app.core.regexp_list import re_pvalue, re_bvalue
from app.core.regexp_list import re_qrfilename

from app.core.slate_login import get_auth_data
from app.core.slate_login import register_authenticated_login

##from app.core.auth import pin_random_ord, pin_prompt_message
from app.core.auth import pin_subset_prompt
from app.core.auth import check_auth_hash
from app.core.auth import authenticate_pin

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
from app.core.messaging import delete_all_messages
from app.core.messaging import message_count

from app.core.mail_temp import temp_mail_send

from app.core.display import yesno
from app.core.display import integer_to_money_format
from app.core.display import integer_to_money_s_format
from app.core.display import integer_to_money_url_format
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
#from flask import Flask, session, g, request
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
from app.forms import InvitationQRForm

from markupsafe import escape

#------------------------------------------------------------------------------
# Shared local functions:

# Create the identity type display string:
def fph_to_display_type(agent_id):
    agent_fph, agent_hrns, etypes, \
    m = identify_entity(agent_id)
    if "primid" in etypes:
        return "login identity"
    else:
        return ""

#------------------------------------------------------------------------------

development_mode = False


# registration ----------------------------------------------------------------
@app.route("/register", methods = ["GET", "POST"])
def register():
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
    page = "register"
    session["previous_page"] = page
    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    if logged_in:
        flash("You cannot register while logged in")
        return redirect("/home_ahc")

    # This one may not be needed:
    mode = "logged_out"

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    #--------------------------------------------------------------------------
    # The following seven variables determine which of the registration form's
    # fields are displayed:
    address_details_included = get_config("address_details_included")
    location_details_included = get_config("location_details_included")
    phone_details_included = get_config("phone_details_included")
    recovery_questions_included = get_config("recovery_questions_included")
    notification_option_included = get_config("notification_option_included")
    country_included = get_config("country_included")
    ssh_public_key_allowed = get_config("ssh_public_key_allowed")
    #address_details_included = False
    #location_details_included = False
    #phone_details_included = False
    #recovery_questions_included = False
    #notification_option_included = False
    #country_included = False
    #ssh_public_key_allowed = False
    #--------------------------------------------------------------------------

    url_currency_id = request.args.get("c")
    initial_namespace_id = request.args.get("s")

    initial_currency_fph, initial_currency_hrns, etypes, \
    m = identify_entity(request.args.get("c"))
    if not (initial_currency_fph and ("currency" in etypes)):
        initial_currency_fph = ""
        initial_currency_hrns = ""

    initial_namespace_fph, initial_namespace_hrns, etypes, \
    m = identify_entity(request.args.get("s"))
    if not initial_namespace_fph:
        initial_namespace_fph = ""
        initial_namespace_hrns = ""

    form = RegistrationForm()

    # The fields displayed depend upon the policy set by the stewards of the
    # initial *currency* and *namespace*. For example, for some *currencies*
    # (many perhaps) it may be considered very useful to have some information
    # about the geographical location of the user's base (home or business
    # address), particularly where this is going to be used to create a map
    # overlay.

    if form.validate_on_submit():

        username = form.username.data

        if initial_namespace_fph == "":
            namespace_id = form.namespace.data.strip().lstrip(".")
        else:
            namespace_id = initial_namespace_fph

        if initial_currency_fph == "":
            currency_id = form.currency.data.strip()
        else:
            currency_id = initial_currency_fph

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

        currency_fph, currency_hrns, etypes, \
        m = identify_entity(currency_id)
        if m:
            log_event("error", "currency", m)
            flash("Invalid currency specified")
            return redirect("/register")
        if not currency_fph:
            flash("No valid currency identifier provided")
            return redirect("/register")
        if not ("currency" in etypes):
            flash(currency_id + " is not a currency")
            return redirect("/register")

        # Similarly, at this point the parent *namespace* may have been
        # specified in either the URL or the form. If the parent *namespace*
        # FPH was specified in the URL, the *currency* HRNS field will not have
        # been displayed.

        # The identify_entity( ) function determines whether either is valid.
        namespace_fph, namespace_hrns, etypes, \
        m = identify_entity(namespace_id)
        if m:
            log_event("error", "namespace", m)
            flash("Invalid parent namespace specified")
            return redirect("/register")
        if not namespace_fph:
            flash("The namespace specified does not exist")
            return redirect("/register")
        if not ("namespace" in etypes):
            flash(namespace_id + ": invalid parent namespace")
            return redirect("/register")

        if form.password_repeat.data != form.password.data:
            flash("The passwords not not match")
            return redirect("/register")

        primid_fph, primid_hrns, access_token, \
        m = new_primid(
                form.username.data,
                namespace_fph,
                form.realname.data,
                form.email_1.data,
                form.email_2.data,
                form.password.data,
                form.pin.data,
                currency_id
            )
        if m:
            log_event("error", "primid creation", m)
            flash(m)
            return redirect("/register")
        flash(
            "A login identity, an account-holder identity, a currency and a " \
            + "namespace have been created using the identifier "
            + primid_hrns + "."
        )

        currency_fph, currency_hrns, active, open, private, sandbox, \
        type, category, units, metrical_equivalence, dimensions, \
        prefix, suffix, default_account_name, stewards_list, \
        m = get_currency_properties(currency_fph)
        if m:
            flash(m)
            return redirect("/register")
        if currency_fph == "":
            flash("The currency specified does not exist.")
            return redirect("/register")

        # If in slate mode, an initial *currency*|*ahid* pairing is created
        # using the new *login identity* (*primid*) as the *ahid*:
        if hub_mode == "slate":
            a_fph = new_pairing(primid_fph, primid_hrns, currency_hrns)
            return redirect("/")

        # Otherwise, an initial *account* is created (in the new *primid*'s
        # private *namespace*) using the default name associated with the
        # specified *currency*.
        else:
            account_fph, account_hrns, \
            m = new_account(
                    default_account_name,
                    primid_fph,
                    primid_fph,
                    currency_fph
                )
            if m:
                log_event("error", "account creation", m)
                flash("The account cannot be created. See error log.")
                return redirect("/register")
            flash(account_hrns + " created in currency " + currency_hrns)
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
        hub_mode = "slate",
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
    session["previous_page"] = page
    mode = "logged_out"
    logged_in = False
    if current_user.is_authenticated: # user is already logged in
        mode = "logged_in"
        logged_in = True
        return redirect(url_for("home_ahc"))

    session["show_top_menu"] = False
    session["show_extended_menu"] = False

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    pin_prompt, pin_subset_indices = pin_subset_prompt()

    form = LoginForm()
    if form.validate_on_submit():

        agent_id = form.identity.data # HRNS or FPH

        if (agent_id == "") and (email == ""): # neither provided
            flash("Either an identity or an email address must be provided")
            return redirect(url_for("login"))

        primid_has_been_identified_from_identity = False
        primid_has_been_identified_from_email = False

        if agent_id:
            identity_fph, identity_hrns, etypes, \
            m = identify_entity(form.identity.data)
            if m:
                flash(m)
                return redirect(url_for("login"))
            if not ("primid" in etypes):
                flash("Invalid identity entered")
                return redirect(url_for("login"))
            if not ("primid" in etypes):
                # authentication requires primary *identity*
                primid_fph, m = get_primid(identity_fph)
                if m:
                    flash(m)
                    log_event(
                        "errors", "primid entification",
                        "The primid cannot be identified from " + identity_fph
                    )
            else:
                primid_fph = identity_fph
        else:
            flash("No valid identifier has been provided.")
            return redirect(url_for("login"))

        password_hash, stored_pin, access_token_hash, \
        m = get_auth_data(primid_fph)
        if m:
            flash(m)
            return redirect(url_for("login"))

        # Retrieve the user object:
        user = User(primid_fph)

        password = form.password.data
        password2 = form.password.data.strip()

        pwd = password
        pwd_hash = password_hash
        if not bcrypt.checkpw(pwd.encode("utf-8"), pwd_hash.encode("utf-8")):
            return redirect(url_for("login"))

        if not authenticate_pin(stored_pin, form.pse.data, form.pro.data):
            flash("Incorrect PIN digits")
            return redirect(url_for("login"))

        # Register the authenticated login:
        register_authenticated_login(primid_fph)

        login_user(user, remember = form.remember_me.data)

        session["login_identity"] = identity_fph   # Initial values upon login
        session["working_identity"] = identity_fph #

        return redirect(url_for("home_ahc"))

    return render_template(
        "login.html",
        title = "Sign in",
        page = page,
        mode = mode,
        hub_mode = "slate",
        version = get_version(),
        logged_in = logged_in,
        form = form,
        development_mode = development_mode
    )

# log out ---------------------------------------------------------------------
@app.route("/logout")
@login_required
def logout():
    user = current_user.get_id()
    logout_user() # a Flask function
    return redirect(url_for("login"))

# login recovery request ------------------------------------------------------
@app.route("/login/recover", methods = ["GET", "POST"])
def login_recover():
    if current_user.is_authenticated: # should be false
        return redirect(url_for("login"))

    page = "login_recovery"
    session["previous_page"] = page
    mode = "logged_out"

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    form = LoginRecoveryForm()
    if form.validate_on_submit():
        agent_id = form.identity.data
        agent_email = form.email.data

        agent_fph, agent_hrns, etypes, \
        m = identify_entity(agent_id)
        if "primid" in etypes:
            agent_primid_fph = agent_fph
        else:
            flash(agent_id + " is not a registered identity")
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
                + "for user " + agent_id
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

        message_body = "You have received this message because a login " \
                     + " recovery link has been requested.\n" \
                     + "\nTo reset your password and PIN, click on:\n" \
                     + login_reset_url + " (or copy and paste it into your " \
                     + "browser's address bar.\n\n" \
                     + "\nIf you have not requested a login recovery " \
                     + "link, you can ignore this message.\n\n"

        temp_mail_send(
            get_config("hub_email"),
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
        hub_mode = "slate",
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
    session["previous_page"] = page
    mode = "logged_out"

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(user_id) # from slug

    password_hash, stored_pin, access_token_hash, \
    m = get_auth_data(user_id) # from URL slug

    serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
    reset_token_data = serializer.loads(
                            token,
                            #max_age = 900,
                            #max_age = app.config["RESET_PASS_TOKEN_MAX_AGE"],
                            salt = password_hash
                        )

    if reset_token_data != primid_fph:
        flash("Login reset token error")
        return redirect("/login")

    form = LoginResetForm()
    if form.validate_on_submit():
        flash("Registration submitted for user " + fph_to_hrns(user_id))
        if form.password_repeat.data != form.password.data:
            flash("The passwords not not match")
            return redirect("/login")

        m = update_primid_access_details(
                primid_fph,
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
        primid_hrns = primid_hrns,
        form = form,
        hub_mode = "slate",
        version = get_version()
    )


@app.route("/hold")
@login_required
def hold():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    if hub_mode != "slate":
        flash("Operational mode invalid for this endpoint")
        return redirect("/home_ahc")

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

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    # In slate mode, the working *identity* is always the *primid*.
    working_identity_fph = primid_fph
    working_identity_hrns = primid_hrns
    working_identity_type = "primid"

    return render_template(
        "hold.html",
        title = "Hold",
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        logged_in = logged_in,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type
    )


@app.route("/toggle_menu")
@login_required
def toggle_menu():
    session["show_top_menu"] = not session["show_top_menu"]
    return redirect("/home_ahc")

@app.route("/toggle_more")
@login_required
def toggle_more():
    session["show_extended_menu"] = not session["show_extended_menu"]
    return redirect("/home_ahc")






@app.route("/home_ahp/<payer_ahid_fph>/<p_currency_fph>/<payer_balance>",
           methods=["GET", "POST"])
@app.route("/home_ahc", methods=["GET", "POST"])
@login_required
def home_ahc(payer_ahid_fph=None, p_currency_fph=None, payer_balance=None):

    page = "home_ahc"
    session["previous_page"] = page

    if not ("show_top_menu" in session.keys()):
        show_top_menu = False
        session["show_top_menu"] = show_top_menu
    show_top_menu = session["show_top_menu"]

    show_payment_form = True

    if (payer_ahid_fph is None):
        payer_ahid_fph = ""
        payer_ahid_hrns = ""
        p_etypes = []
        show_payment_form = False
    else:
        payer_ahid_fph, payer_ahid_hrns, p_etypes, \
        m = identify_entity(payer_ahid_fph)
        if not ("ahid" in p_etypes):
            flash("Invalid payer: " + p_currency_hrns)
            show_payment_form = False

    if (p_currency_fph is None):
        p_currency_fph = ""
        p_currency_hrns = ""
        c_etypes = []
        show_payment_form = False
    else:
        p_currency_fph, p_currency_hrns, c_etypes, \
        m = identify_entity(p_currency_fph)
        if not p_currency_fph:
            flash("Unregistered currency identifier")
            show_payment_form = False
        elif not ("currency" in c_etypes):
            flash("Invalid currency: " + p_currency_hrns)
            show_payment_form = False

    if not (payer_balance is None):
        #if not payer_balance.isnumeric():
        if not re_bvalue.match(payer_balance):
            flash("Invalid balance value: " + payer_balance)
            show_payment_form = False
    else:
        show_payment_form = False

    # If a dataset import if in progress, do not allow any FPH>HRNS or
    # HRNS>FPH mapping operations to be initiated by a browser refresh.
    # Instead, display a holding page.
    if os.path.exists(IMPORTING):
        return redirect("/hold")

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    if hub_mode != "slate":
        flash("Operational mode invalid for this endpoint")
        return redirect("/home_ahc")

    if show_payment_form:
        page = "home_ahp"
    else:
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

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    # In slate mode, the working *identity* is always the *primid*.
    working_identity_fph = primid_fph
    working_identity_hrns = primid_hrns
    working_identity_type = "primid"

    nstewardships_list, m = list_namespace_stewardships(primid_fph)
    cstewardships_list, m = list_currency_stewardships(primid_fph)

    pmap_t, m = retrieve_pmap(primid_fph)

    # List all *ahid*:
    ahid_list = []
    for ahid_hrns in pmap_t.keys():
        ahid_list.append(ahid_hrns)

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    p_rows = []

    # First count the number of occurrences of each *currency*:
    currency_count = {}
    for ahid_hrns in pmap_t.keys():
        for currency_hrns in pmap_t[ahid_hrns].keys():
            if currency_hrns in currency_count.keys():
                currency_count[currency_hrns] += 1
            else:
                currency_count[currency_hrns] = 1
    currency_displayed_already = {}
    for currency_hrns in currency_count.keys():
        currency_displayed_already[currency_hrns] = False

    for ahid_hrns in pmap_t.keys():
        for currency_hrns in pmap_t[ahid_hrns].keys():

            account_fph = pmap_t[ahid_hrns][currency_hrns]

            account_currency_fph, account_owner_fph, \
            account_balance, account_volume, account_active, \
            account_type, account_category, account_units, \
            account_metrical_equivalence, account_dimensions, \
            m = get_account_properties(account_fph)

            if fph_to_hrns(account_currency_fph) != currency_hrns:
                continue # (This should never happen)

            currency_fph, currency_hrns, currency_active, open, private, \
            sandbox, type, category, units, metrical_equivalence, dimensions, \
            prefix, suffix, default_account_name, stewards_list, \
            m = get_currency_properties(account_currency_fph)

            if currency_active:
                p_row = {}
                p_row["currency_hrns"] = currency_hrns
                p_row["ahid_hrns"] = ahid_hrns
                p_row["ahid_fph"], m = hrns_to_fph(ahid_hrns)
                p_row["account_fph"] = account_fph
                p_row["account_owner_fph"] = account_owner_fph
                p_row["account_owner_hrns"] = fph_to_hrns(account_owner_fph)
                p_row["balance"] = integer_to_money_format(account_balance)
                p_row["p_balance"] = integer_to_money_s_format(account_balance)
                p_row["isneg"] = (account_balance < 0)
                p_row["prefix"] = prefix
                p_row["suffix"] = suffix
                #p_row["volume"] = integer_to_money_format(account_volume)
                if currency_fph in cstewardships_list:
                    p_row["primid_currency_steward"] = True
                else:
                    p_row["primid_currency_steward"] = False
                p_row["currency_fph"] = currency_fph
                p_row["pairing_selected"] = False
                if (currency_hrns == p_currency_hrns):
                    if (ahid_hrns == payer_ahid_hrns):
                        p_row["pairing_selected"] = True
                p_rows.append(p_row)

    # Sorting by *currency* and *ahid* (quick and dirty method)
    currencies_list = []
    for row in p_rows:
        currency = row["currency_hrns"]
        if not(currency in currencies_list):
            currencies_list.append(currency)
    currencies_list.sort()
    ahid_lists_dict = {}
    for currency in currencies_list:
        ahid_lists_dict[currency] = []
        for row in p_rows:
            ahid = row["ahid_hrns"]
            if not(ahid in ahid_lists_dict[currency]):
                ahid_lists_dict[currency].append(ahid)
        ahid_lists_dict[currency].sort()
    p_rows2 = []
    for currency in currencies_list:
        for ahid in ahid_lists_dict[currency]:
            for row in p_rows:
                if (row["currency_hrns"] == currency) and \
                   (row["ahid_hrns"] == ahid):
                    if currency_displayed_already[currency]:
                        row["blank_currency_cell"] = True
                    else:
                        row["blank_currency_cell"] = False
                        row["currency_count"] = currency_count[currency]
                        currency_displayed_already[currency] = True
                    p_rows2.append(row)

    form = SpecifyPayeeAccountHolderForm()
    if form.validate_on_submit():
        payee_ahid_fph, payee_ahid_hrns, etypes, \
        m = identify_entity(form.payee_ahid.data) # HRNS or FPH
        if m:
            flash(m)
            return redirect(
                #"/pay_to_ahid/" + payer_ahid_fph + "/" + currency_fph
                "/home_ahp/" + payer_ahid_fph + "/" + currency_fph + "/" \
                + payer_balance
            )
        if payee_ahid_fph == "":
            flash("The specified account-holder does not exist")
            return redirect(
                #"/pay_to_ahid/" + payer_ahid_fph + "/" + currency_fph
                "/home_ahp/" + payer_ahid_fph + "/" + currency_fph + "/" \
                + payer_balance
            )
        if not get_ahid_primid(payee_ahid_hrns):
            flash("The payee specified is not an account-holder")
            return redirect(
                #"/pay_to_ahid/" + payer_ahid_fph + "/" + currency_fph
                "/home_ahp/" + payer_ahid_fph + "/" + currency_fph + "/" \
                + payer_balance
            )

        amount = int(round(float(form.amount.data)*100))
        annotation = form.annotation.data

        m = ah_payment(
                payer_ahid_hrns,
                payee_ahid_hrns,
                p_currency_hrns,
                amount,
                annotation
            )
        if m:
            flash(m)
        else:
            flash(
                integer_to_money_s_format(amount) \
                + " paid from " + payer_ahid_hrns \
                + " to " + payee_ahid_hrns \
                + " in " + p_currency_hrns
            )
            if annotation:
                flash("(" + annotation + ")")

        return redirect("/home_ahc")

    return render_template(
        "home_ahc.html",
        title = "Home",
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        development_mode = development_mode,
        logged_in = logged_in,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        p_rows = p_rows2,
        pmap_t = pmap_t,
        form = form,
        show_top_menu = show_top_menu,
        display_in_from_lines = False,
        show_payment_form = show_payment_form,
        p_currency_hrns = p_currency_hrns,
        payer_ahid_hrns = payer_ahid_hrns,
        payer_balance = payer_balance,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
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

    page = "list_accounts"
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

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = "primid"
    working_identity_type = etype_to_adtype(working_identity_type)

    # The user logs in as the *primid*, but once logged in will see all of its
    # *identities* along with
    # a list of *accounts* belonging to each. The user will also see a list of
    # entities over which it holds/shares stewardship.

    nstewardships_list, m = list_namespaces_stewardships(primid_fph)
    cstewardships_list, m = list_currency_stewardships(primid_fph)

    # Since a user may have *accounts* scattered across an arbitrary number of
    # *namespaces*, it is necessary to maintain a list of these:

    # A full list of *identities* is compiled, with the *primid* first:

    identities = [] # list of *identity* dictionaries) to "home.html" template.

    for id_fph in identities_list:

        id = {} # the outer dictionary for this *identity*

        id_fph, id_hrns, etypes, \
        m = identify_entity(id_fph)
        if m:
            flash(m)

        id["fph"] = id_fph
        id["hrns"] = fph_to_hrns(id_fph)
        if "primid" in etypes:
            id["type"] = "login identity"
        else:
            flash("Invalid identity type found")
            return redirect("/home_ahc")

        accounts_list, m = list_agent_accounts(id_fph)
        if m:
            flash(m)

        # List the *accounts* belonging to this *identity*:
        accounts = [] # (second-level dictionary for iteration in template)
        for account_fph in accounts_list:
            # Fetch account details:
            account_currency_fph, account_owner_fph, \
            account_balance, account_volume, active, \
            account_type, account_category, account_units, \
            account_metrical_equivalence, account_dimensions, \
            m = get_account_properties(account_fph)

            # Fetch currency details:
            currency_fph, currency_hrns, active, open, private, sandbox, \
            type, category, units, metrical_equivalence, dimensions, \
            prefix, suffix, default_account_name, stewards_list, \
            m = get_currency_properties(account_currency_fph)

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
            if currency_fph in cstewardships_list:
                primid_currency_steward = True
            else:
                primid_currency_steward = False
            a["primid_is_currency_steward"] = primid_currency_steward
            a["currency_fph"] = currency_fph
            a["currency_hrns"] = currency_hrns
            accounts.append(a)

        id["accounts"] = accounts
        identities.append(id)

    nstewardships = []
    for nstewardship_fph in nstewardships_list:
        if nstewardship_fph != "":
            nstewardship = {}
            entity_fph, entity_hrns, etypes, \
            m = identify_entity(nstewardship_fph)
            nstewardship["fph"] = nstewardship_fph
            nstewardship["hrns"] = entity_hrns
            nstewardship["etype"] = etype
            nstewardships.append(stewardship)

    cstewardships = []
    for cstewardship_fph in cstewardships_list:
        if cstewardship_fph != "":
            cstewardship = {}
            entity_fph, entity_hrns, etypes, \
            m = identify_entity(cstewardship_fph)
            cstewardship["fph"] = cstewardship_fph
            cstewardship["hrns"] = entity_hrns
            cstewardship["etype"] = etype
            cstewardships.append(stewardship)

    return render_template(
        "list_accounts.html",
        title = "List accounts",
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        development_mode = development_mode,
        logged_in = logged_in,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,

        # List of (nested) dictionaries for display in "home.html":
        identities = identities,
        nstewardships = nstewardships,
        cstewardships = cstewardships
     )

#==============================================================================
#
@app.route("/pay_to_ahid/<payer_ahid_fph>/<payment_currency_fph>",
           methods = ["GET", "POST"])
@login_required
def pay_ahid(payer_ahid_fph, payment_currency_fph):

    payer_ahid_fph, payer_ahid_hrns, etypes, \
    m = identify_entity(payer_ahid_fph)

    if payer_ahid_fph == "":
        flash("Invalid payer account-holder")
        return redirect("/home_ahc")

    currency_fph, currency_hrns, etypes, \
    m = identify_entity(payment_currency_fph)

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "pay_ahid"
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    previous_page = session["previous_page"] # Ensure correct page sequence
    session["previous_page"] = page

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())
    working_identity_fph = primid_fph
    working_identity_hrns = primid_hrns
    working_identity_type = "primid"

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    form = SpecifyPayeeAccountHolderForm()
    if form.validate_on_submit():
        payee_ahid_fph, payee_ahid_hrns, etypes, \
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
            flash("The payee specified is not an account-holder")
            return redirect(
                       "/pay_to_ahid/" + payer_ahid_fph + "/" + currency_fph
                   )

        amount = int(round(float(form.amount.data)*100))
        annotation = form.annotation.data

        m = ah_payment(
                payer_ahid_hrns,
                payee_ahid_hrns,
                currency_hrns,
                amount,
                annotation
            )
        if m:
            flash(m)

        return redirect("/home_ahc")

    return render_template(
        "pay_to_ahid.html",
        title = "Make a payment to an account-holder",
        page = page,
        group = group,
        form = form,
        logged_in = logged_in,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        payer_ahid_hrns = payer_ahid_hrns,
        currency_hrns = currency_hrns,
        number_of_indelible_messages = number_of_indelible_messages,
        number_of_messages = number_of_messages
    )




#==============================================================================
#
@app.route("/journal/<ahid_fph>/<currency_fph>", methods = ["GET", "POST"])
@login_required
def journal(ahid_fph, currency_fph):

    ahid_fph, ahid_hrns, etypes, \
    m = identify_entity(ahid_fph)
    if ahid_fph == "":
        flash("Invalid account-holder")
        return redirect("/home_ahc")

    currency_fph, currency_hrns, etypes, \
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

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    working_identity_fph = primid_fph
    working_identity_hrns = primid_hrns
    working_identity_type = "primid"

    account_fph, primid_fph, \
    m = retrieve_pairing_account_fph(ahid_hrns, currency_fph)

    account_currency_fph, account_owner_fph, account_balance, account_volume, \
    account_active, account_type, account_category, account_units, \
    account_metrical_equivalence, account_dimensions, \
    m = get_account_properties(account_fph)

    with sqlite3.connect(PAYMENTS_DB) as conn:
        cursor = conn.cursor()
        # Read transactions for specified currency:
        cursor.execute(
            "SELECT " \
            + "timestamp, " \
            + "payment_id, " \
            + "payer_fph, " \
            + "payee_fph, " \
            + "currency_fph, " \
            + "amount, " \
            + "payer_balance, " \
            + "payee_balance, " \
            + "annotation " \
            + "FROM payments " \
            + "WHERE (payer_fph = ? OR payee_fph = ?) and (currency_fph = ?)",
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
        p_time = ":".join(p_time_)

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

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    return render_template(
        "transaction_journal_ahc.html",
        title = "Display transaction journal",
        page = page,
        group = group,
        logged_in = logged_in,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        ahid_hrns = ahid_hrns,
        currency_hrns = currency_hrns,
        journal_rows = journal_rows,
        account_fph = account_fph,
        account_volume = integer_to_money_format(account_volume),
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
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



# stewardships page ----------------------------------------------------------
@app.route("/stewardships/<identity_fph>")
@login_required
def stewardships(identity_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

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

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    stewardships, m = list_stewardships(primid_fph)
    if m:
        splash(m)

    return render_template(
        "stewardships.html",
        title = "Stewardships",
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
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






@app.route("/currency/<currency_fph>", methods = ["GET", "POST"])
@login_required
def currency(currency_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "currency"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    currency_fph, currency_hrns, etypes, \
    m = identify_entity(currency_fph)
    if (not ("currency" in etypes)):
        return "", "", currency_fph + " is not a currency"

    currency_fph, currency_hrns, active, open, private, sandbox, \
    type, category, units, metrical_equivalence, dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_fph)

    # Compile a list of the stewards of this *currency*, excluding the *primid*
    # of the *agent* logged in here:
    current_stewards = []
    for steward_fph in stewards_list:
        if steward_fph != primid_fph:
            s = {}
            s["fph"] = steward_fph
            s["hrns"] = fph_to_hrns(steward_fph)
            current_stewards.append(s)

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    return render_template(
        "currency.html",
        title = "Currency",
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        currency_fph = currency_fph,
        currency_hrns = currency_hrns,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        current_stewards = current_stewards,
        development_mode = development_mode,
        logged_in = logged_in,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
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

    primid_fph, primid_hrns, etype, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns

    currency_fph, currency_hrns, active, open, private, sandbox, \
    type, category, units, metrical_equivalence, dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_fph)

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    form = StewardAddForm()
    if form.validate_on_submit():
        steward_fph, steward_hrns, etypes, \
        m = identify_entity(form.new_steward.data)
        if steward_fph:
            m = add_currency_stewardship(currency_fph, steward_fph, primid_fph)
        else:
            flash(form.new_steward.data + " is not a registered identity")

        if hub_mode == "slate":
            return redirect("/home_ahc")
        else:
            return redirect("/home_ahc")

    return render_template(
        "currency_steward_add.html",
        title = "Add currency steward",
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        form = form,
        currency_fph = currency_fph,
        currency_hrns = currency_hrns,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        stewards_list = stewards_list,
        logged_in = logged_in,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
    )

#
@app.route("/currency/steward/remove/<currency_fph>/<steward_fph>",
           methods = ["GET", "POST"]
#           methods = ["GET"]
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

    currency_fph, currency_hrns, etypes, m = identify_entity(currency_fph)
    steward_fph, steward_hrns, etypes, m = identify_entity(steward_fph)
    primid_fph, primid_hrns, etypes, m = identify_entity(current_user.get_id())

    if not steward_fph:
        flash("Steward does not exist - cannot remove")
        return redirect("/home_ahc")
    if not currency_fph:
        flash("Currency does not exist - cannot remove steward")
        return redirect("/home_ahc")
    if steward_fph == primid_fph:
        flash("Cannot remove this primid from stewardship")
        return redirect("/home_ahc")

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    currency_fph, currency_hrns, active, open, private, sandbox, \
    type, category, units, metrical_equivalence, dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_fph)

    if steward_fph in stewards_list:
        m = remove_currency_stewardship(currency_fph, steward_fph, primid_fph)

    return redirect("/home_ahc")

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

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    return render_template(
        "manage.html",
        title = "Manage your SLATE settings",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
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

    page = "create_currency"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = True
    logged_in = current_user.is_authenticated

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_type = session["working_identity"]
        working_identity_fph = primid_fph
        working_identity_hrns = primid_hrns
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    form = CurrencyCreateForm()
    if form.validate_on_submit():
        namespace_fph, namespace_hrns, etypes, \
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

        currency_fph, currency_hrns, \
        m = new_currency(
                currency_name,
                namespace_fph,
                primid_fph,
                form.prefix_symbol.data,
                form.suffix_symbol.data,
                form.default_account_name.data,
                "scalar",
                "money",
                "unspecified",
                "lt",
                "unspecified"
            )
        flash(
            "A new currency has been created: " + currency_hrns
        )

        return redirect("/home_ahc")

    return render_template(
        "create_currency.html",
        title = "Create a currency",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = "slate",
        create_currency_form_full = get_config("create_currency_form_full"),
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        form = form,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = etype_to_adtype(working_identity_type),
        development_mode = development_mode,
        namespace_steward = namespace_steward,
        currency_steward = currency_steward,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
    )

# create an *ahid*-*currency* pairing -----------------------------------------
#@app.route("/create_ahid/<owner_fph>", methods = ["GET", "POST"])
@app.route("/create_pairing/<owner_fph>", methods = ["GET", "POST"])
@login_required
def create_pairing(owner_fph = ""):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    if hub_mode != "slate":
        flash("Invalid operational mode for this endpoint")
        return redirect("/home_ahc")

    page = "create_pairing"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = True
    logged_in = current_user.is_authenticated

    if owner_fph:
        owner_fph, owner_hrns, owner_type, \
        m = identify_entity(owner_fph)
        if m:
            flash(m)
            return redirect("/home_ahc")
        if owner_fph == "":
            flash("The owner FPH in the URL cannot be identified")
            return redirect("/home_ahc")

    if hub_mode != "slate":
        flash("This endpoint is not valid in the current mode.")
        return redirect("/home_ahc")

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    # In slate mode the *working identity* is always the *primary identity*.
    working_identity_fph = primid_fph
    working_identity_hrns = primid_hrns
    working_identity_type = "primid"

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    form = PairingCreateForm()
    if form.validate_on_submit():

        ahid_hrns = form.ahid_hrns.data.strip()
        if not re_hrns.match(ahid_hrns):
            flash(ahid_hrns + " is not a valid identifier string")
            return redirect("/create_pairing/" + owner_fph)
            #return redirect("/create_ahid/" + owner_fph)
        if not is_in_private_namespace(ahid_hrns, owner_hrns):
        #if not is_ancestor(ahid_hrns, owner_hrns):
            flash(ahid_hrns + " is not in private namespace of " + owner_hrns)
            return redirect("/create_pairing/" + owner_fph)

        currency_id = form.currency_id.data

        currency_fph, currency_hrns, etypes, \
        m = identify_entity(currency_id)
        if m:
            flash(m)
            return redirect("/home_ahc")
        if not ("currency" in etypes):
            flash(currency_id + " is not a currency")
            #return redirect("/home_ahc")
            return redirect("/create_pairing/" + owner_fph)
            #return redirect("/create_ahid/" + owner_fph)

        currency_fph, currency_hrns, active, open, private, sandbox, \
        type, category, units, metrical_equivalence, dimensions, \
        prefix, suffix, default_account_name, stewards_list, \
        m = get_currency_properties(currency_fph)

        account_fph = new_pairing(
                          working_identity_fph,
                          ahid_hrns,
                          currency_hrns
                      )

        if hub_mode == "slate":
            return redirect("/home_ahc")
        else:
            return redirect("/home_ahc")

    return render_template(
        "create_ahid_currency_pair.html",
        title = "Pair an account-holder with a currency",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        form = form,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        development_mode = development_mode,
        namespace_steward = namespace_steward,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
    )


# create a new namespace ------------------------------------------------------
@app.route("/create_namespace", methods = ["GET", "POST"])
@login_required
def create_namespace():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "create_namespace"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    paying = True
    logged_in = current_user.is_authenticated

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = etype_to_adtype(working_identity_type)

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    form = NamespaceCreateForm()
    if form.validate_on_submit():
        parent_fph, parent_hrns, etypes, \
        m = identify_entity(form.parent_namespace_id.data.strip().lstrip("."))
        if not parent_fph:
            flash("Parent namespace does not exist")
            return redirect("/create_namespace")

        inh_default_currency_fph = get_default_currency(parent_fph)

        namespace_name = form.namespace_name.data
        # Check whether an entity with the proposed HRNS exists already.
        proposed_hrns = namespace_name + "." + parent_hrns
        if hrns_exists_already(proposed_hrns):
            flash(proposed_hrns + " is already registered")
            return redirect("/create_namespace")

        namespace_fph, namespace_hrns,\
        m = new_namespace(
                namespace_name,
                parent_fph,
                "cc", # TEMPORARY
                #default_currency_fph,
                primid_fph
            )
        flash(
            "A new namespace has been created, identified as \n" \
            + namespace_hrns
        )
        return redirect("/home_ahc")

    return render_template(
        "create_namespace.html",
        title = "Create a namespace",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        form = form,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
    )

# list the existing namespaces ------------------------------------------------
@app.route("/list_namespaces", methods = ["GET", "POST"])
@login_required
def list_namespaces():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "list_namespaces"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    namespace_steward = False
    currency_steward = False
    logged_in = current_user.is_authenticated

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
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
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        available_namespaces = available_namespaces
    )

# add steward to entitity =====================================================
@app.route("/steward/add/<entity_fph>", methods = ["GET", "POST"])
@login_required
def add_steward():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "add_steward"
    previous_page = session["previous_page"]
    session["previous_page"] = page
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = "primid"
    working_identity_type = etype_to_adtype(working_identity_type)

    # The entity (*namespace* or *currency* to which this new steward is to be
    # added):

    entity_fph, entity_hrns, etypes, \
    m = identify_entity(entity_fph) # slug
    if m:
        flash(m)
        return redirect("/home_ahc")
    if entity_fph == "":
        flash("The entity specified does not exist")
        return redirect("/home_ahc")
    if "namespace" in etypes:
        namespace_exists, namespace_private, namespace_active, stewards_list, \
        m = namespace_status(namespace_fph)
    elif "currency" in etypes:
        currency_fph, currency_hrns, active, open, private, sandbox, \
        type, category, units, metrical_equivalence, dimensions, \
        prefix, suffix, default_account_name,  stewards_list, \
        m = get_currency_properties(currency_fph)
    else:
        flash("The entity specified is not of a stewarded type")
        return redirect("/home_ahc")

    form = StewardAddForm()
    if form.validate_on_submit():
        steward_fph, steward_hrns, etypes, \
        m = identify_entity(form.new_steward.data)
        if m:
            flash(m)
            return redirect("/currency/" + currency_fph)
        if "primid" in etypes:
            stewards_list.append(primid_fph)
            with sqlite3.connect(ENTITIES_DB) as conn:
                cursor = conn.cursor()
                if "namespace" in etypes:
                    cursor.execute(
                        "UPDATE namespaces SET stewards_fph_list = ? " \
                        + "WHERE entity_fph = ?",
                        (pickle.dumps(stewards_list), namespace_fph)
                    )
                elif "currency" in etypes:
                    cursor.execute(
                        "UPDATE currencies SET stewards_fph_list = ? " \
                        + "WHERE entity_fph = ?",
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

    page = "export_account"
    previous_page = session["previous_page"]
    session["previous_page"] = page
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if hub_mode == "slate":
        working_identity_fph = primid_fph
        working_identity_hrns = primid_hrns
        working_identity_type = "primid"
    elif "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = "primid"
    working_identity_type = etype_to_adtype(working_identity_type)

    account_fph, account_hrns, etypes, \
    m = identify_entity(account_fph) # slug
    if m:
        flash(m)
        return redirect("/home_ahc")
    if not account_fph:
        flash(account_fph + " is not a registered identifier")
        return redirect("/home_ahc")
    if not ("account" in etypes):
        flash(account_hrns + " has no registered account")
        return redirect("/home_ahc")

    currency_fph, owner_fph, balance, volume, active, \
    account_type, account_category, account_units, \
    account_metrical_equivalence, account_dimensions, \
    m = get_account_properties(account_fph)
    if m:
        flash(m)
        return redirect("/home_ahc")
    ahid_hrns = fph_to_hrns(owner_fph)

    owner_fph, owner_hrns, etypes, \
    m = identify_entity(owner_fph)
    if m:
        flash(m)
        return redirect("/home_ahc")
    if ("ahid" in etypes):
        owner_primid_fph, m = get_primid(owner_fph)
    else:
        flash("None of your identities owns this account")
        return redirect("/home_ahc")

    currency_fph, currency_hrns, etypes, \
    m = identify_entity(currency_fph)
    if m:
        flash(m)
        return redirect("/home_ahc")
    if not ("currency" in etypes):
        flash(currency_id + " is not a currency")
        return redirect("/home_ahc")

    csv_file, m = dump_account_payments_csv(account_fph, True)
    if m:
        flash(m)
        return redirect("/home_ahc")

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    return render_template(
        "export_account_journal.html",
        title = "export_account_journal",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        currency_fph = currency_fph,
        currency_hrns = currency_hrns,
        account_fph = account_fph,
        account_hrns = account_hrns,
        #csv_export_path = csv_export_path,
        ahid_fph = owner_fph,
        ahid_hrns = ahid_hrns,
        csv_file = csv_file,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
    )

#------------------------------------------------------------------------------
# Export *currency* journal:
@app.route("/currency/export/<currency_fph>", methods = ["GET", "POST"])
@login_required
def export_currency_csv(currency_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "export_currency"
    previous_page = session["previous_page"]
    session["previous_page"] = page
    group = "home" # Used to control top menu behaviour.
    logged_in = current_user.is_authenticated

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if hub_mode == "slate":
        working_identity_fph = primid_fph
        working_identity_hrns = primid_hrns
        working_identity_type = "primid"
    elif "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = "primid"
    working_identity_type = etype_to_adtype(working_identity_type)

    currency_fph, currency_hrns, etypes, \
    m = identify_entity(currency_fph) # from URL slug
    if m:
        flash(m)
        return redirect("/home_ahc")
    if currency_fph == "":
        flash("The entity specified does not exist")
        return redirect("/home_ahc")
    if not ("currency" in etypes):
        flash("The entity specified is not a currency")
        return redirect("/home_ahc")

    currency_fph, currency_hrns, active, open, private, sandbox, \
    type, category, units, metrical_equivalence, dimensions, \
    prefix, suffix, default_account_name, stewards_list, \
    m = get_currency_properties(currency_fph)
    if m:
        flash(m)
        return redirect("/home_ahc")

    if not (primid_fph in stewards_list):
        flash("You are not a steward of this currency")
        return redirect("/home_ahc")

    csv_file, \
    m = dump_currency_payments_csv(currency_fph, True)
    if m:
        flash(m)
        return redirect("/home_ahc")

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    return render_template(
        "export_currency_journal.html",
        title = "export_currency_journal",
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        currency_fph = currency_fph,
        currency_hrns = currency_hrns,
        #csv_export_path = csv_export_path
        csv_file = csv_file,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
    )



#==============================================================================
# CSV import: sandbox payments set
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



@app.route(
    "/importing/<file>", methods=["GET", "POST"]
)
def importing(file):
    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    if hub_mode != "slate":
        flash("You are working in the wrong mode to use this import function")
        return redirect("/home_ahc")
    page = "dataset_import"
    previous_page = session["previous_page"]
    session["previous_page"] = page
    group = "home" # Used to control top menu behaviour.
    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())
    working_identity_fph = primid_fph
    working_identity_hrns = primid_hrns
    session["working_identity"] = working_identity_fph
    logged_in = current_user.is_authenticated
    if file:
        tfpath = SLATE_TEMP + "/" + file
        if os.path.exists(tfpath):
            flash("Please wait while the CSV file is being processed ...")
            report, errors = import_csv_dataset(tfpath, primid_fph)
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
        hub_mode = "slate",
        version = get_version(),
        logged_in = logged_in,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns
    )

@app.route("/import/dataset", methods = ["GET", "POST"])
@login_required
def import_payment_set():
    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    if hub_mode != "slate":
        flash("You are working in the wrong mode to use this import function")
        return redirect("/home_ahc")
    page = "dataset_import"
    previous_page = session["previous_page"]
    session["previous_page"] = page
    group = "home" # Used to control top menu behaviour.
    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())
    working_identity_fph = primid_fph
    working_identity_hrns = primid_hrns
    session["working_identity"] = working_identity_fph
    logged_in = current_user.is_authenticated

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    if request.method == 'POST':
        if "csv_file" in request.files:
            file = request.files["csv_file"]
            filename = random_filename()
            tfpath = SLATE_TEMP + "/" + filename
            file.save(tfpath)
            with open(IMPORT_QUEUE, "a") as iqf:
                iqf.write(primid_fph + ":" + filename + "\n")
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
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        logged_in = logged_in,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
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

    page = "messages"
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

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = "primid"
    working_identity_type = etype_to_adtype(working_identity_type)

    total_number_of_messages = 0
    total_number_of_indelible_messages = 0
    message_recipients_list = [] # (list of dictionaries for template)

    if hub_mode == "slate":

        pmap_t, m = retrieve_pmap(primid_fph)

        # List all *ahid*:
        ahid_list = []
        for ahid_hrns in pmap_t.keys():
            ahid_list.append(ahid_hrns)
            number_of_messages, \
            number_of_indelible_messages = messages_available(ahid_hrns)
            total_number_of_messages += number_of_messages
            total_number_of_indelible_messages += number_of_indelible_messages
            if number_of_messages > 0:
                m = {}
                m["hrns"] = ahid_hrns
                m["fph"], e = hrns_to_fph(ahid_hrns)
                m["message_count"] = str(number_of_messages)
                if number_of_indelible_messages > 0:
                    m["some_indelible"] = True
                else:
                    m["some_indelible"] = False
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
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        logged_in = logged_in,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
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

    page = "send_message"
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

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = "primid"
    working_identity_type = etype_to_adtype(working_identity_type)

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    form = UserMessageForm()
    if form.validate_on_submit():

        sender_fph, sender_hrns, sender_etypes, \
        m = identify_entity(form.sender.data)
        if not ("ahid" in sender_etypes):
            flash("The specified sender is not an ahid")
            return redirect("/message/send")
        if not sender_fph:
            flash("The specified sender does not exist")
            return redirect("/message/send")
        if get_ahid_primid(sender_fph) != primid_fph:
            flash(sender_hrns + " is not one of your ahid")
            return redirect("/message/send")

        # An *ahid* and a *currency* may share the same identifier, so the
        # "Broadcast" checkbox is used to force interpretation as a *currency*.
        recipient_fph, recipient_hrns, r_etypes, \
        m = identify_entity(form.recipient.data)
        if m:
            flash(m)
            return redirect("/message/send")
        broadcast_to_currency = False
        if form.broadcast.data and ("currency" in r_etypes):
            broadcast_to_currency = True
        elif not ("ahid" in r_etypes):
            flash("Recipient is not a valid ahid")
            return redirect("/messages/send")

        now = datetime.now()
        message_timestamp = now.strftime("%Y-%m-%d_%H:%M:%S")

        date_today = now.strftime("%Y%m%d")

        category = form.category.data

        subject = form.subject.data

        expiry_date = form.expiry_date.data

        expiry_date_ = expiry_date.strftime("%Y%m%d")

        expiry_datetime = expiry_date.strftime("%Y-%m-%d_%H:%M:%S")

        if expiry_date_ < date_today:
            flash("The expiry date cannot be in the past.")

        lifespan = form.lifespan.data
        longevity = lifespan + unixtime_int()
        #unixtime = unixtime_int()

        message_body = form.message_body.data

        em = send_message(
                message_timestamp,
                sender_fph,
                recipient_fph,
                category,
                "",                     # subject_prefix
                subject,                # string
                "",                     # stewardship_id
                longevity,              # integer: lifespan (seconds)
                expiry_datetime,        # string: YYYY-MM-DD_hh:mm:ss
                "",                     # payer_account_fph
                "",                     # payee_account_fph
                "",                     # payer_ahid_fph
                "",                     # payee_ahid_fph
                "",                     # currency_fph
                "",                     # amount
                message_body,           # string
                False,                  # boolean
                broadcast_to_currency   # boolean
            )
        if em:
            flash(em)
            return redirect("/home_ahc")
        else:
            return redirect("/message/list")

    return render_template(
        "message_send.html",
        title = "Send user message",
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        logged_in = logged_in,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        form = form,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
    )


@app.route("/message/show/<recipient_fph>", methods = ["GET", "POST"])
@login_required
def messages_show(recipient_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "show_messages"
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

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if "working_identity" in session:
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
        # TEMPORARY FUDGE ...
        working_identity_type = "primid"
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = "primid"
    working_identity_type = etype_to_adtype(working_identity_type)

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    recipient_fph, recipient_hrns, etypes, \
    m = identify_entity(recipient_fph)
    if len(set(["primid", "ahid"]) & set(etypes)) == 0:
        flash("Recipient is not an agent")
        return redirect("/home_ahc")

    message_list = fetch_messages(recipient_fph)
    any_messages = len(message_list) > 0

    return render_template(
        "messages_show.html",
        title = "Messages",
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        logged_in = logged_in,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        recipient_hrns = recipient_hrns,
        recipient_fph = recipient_fph,
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

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    recipient_fph, recipient_hrns, recipient_types, \
    m = identify_entity(recipient_fph)

    if recipient_fph == "":
        flash("ERROR: recipient is unregistered")
        return redirect("/home_ahc")
    if ("primid" in recipient_types) and (recipient_fph != primid_fph):
        flash("ERROR: recipient is incorrect primid")
        return redirect("/home_ahc")
    elif ("ahid" in recipient_types):
        ahids_list = list_ahids(primid_fph)
        if not (recipient_fph in ahids_list):
            flash("ERROR: recipient ahid does not belong to current primid")
            return redirect("/home_ahc")

    if not isinstance(message_id, str):
        flash("ERROR: invalid message ID in URL")
        return redirect("/home_ahc")

    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
        previous_page = "home_ahc"

    em = delete_message(message_id)
    if em:
        flash(em)

    return redirect("/message/show/" + recipient_fph)


#
# Delete a all messages for user:
#
@app.route("/messages/clear/<recipient_fph>", methods = ["GET", "POST"])
@login_required
def messages_clear(recipient_fph):

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    recipient_fph, recipient_hrns, recipient_types, \
    m = identify_entity(recipient_fph)

    if recipient_fph == "":
        flash("ERROR: recipient is unregistered")
        return redirect("/home_ahc")

    if ("primid" in recipient_types) and (recipient_fph != primid_fph):
        flash("ERROR: recipient is incorrect primid")
        return redirect("/home_ahc")
    elif ("ahid" in recipient_types):
        ahids_list = list_ahids(primid_fph)
        if not (recipient_fph in ahids_list):
            flash("ERROR: recipient ahid does not belong to current primid")
            return redirect("/home_ahc")

    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
        previous_page = "home_ahc"

    delete_all_messages(recipient_fph)

    #return redirect("/message/show/" + recipient_fph)
    return redirect("/message/list")

#==============================================================================
#

@app.route("/invitation/generate", methods = ["GET", "POST"])
@login_required
def invitation_generate():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "create_invitation_qr"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    if (hub_mode != "slate") and ("working_identity" in session):
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = etype_to_adtype(working_identity_fph)

    hub_url = get_config("hub_url")
    if not hub_url:
        flash("hub_url is not defined in hub_config")
        return redirect("/home_ahc")

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    form = InvitationQRForm()
    if form.validate_on_submit():

        namespace_fph, namespace_hrns, etypes, \
        m = identify_entity(form.namespace_id.data)
        if namespace_fph == "":
            flash("Invalid namespace")
            return redirect("/invitation/generate")

        currency_fph, currency_hrns, etypes, \
        m = identify_entity(form.currency_id.data)
        if currency_fph == "":
            flash("Invalid currency")
            return redirect("/invitation/generate")

        qrcf = qrencode_invitation(currency_fph, namespace_fph, primid_fph)

        return redirect("/invitation/showqr/" + qrcf)

    return render_template(
        "invitation.html",
        title = "Create invitation QR code",
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        logged_in = logged_in,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        form = form,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages
    )


#
@app.route("/invitation/showqr/<qrfilename>", methods = ["GET", "POST"])
@login_required
def invitation_display(qrfilename):

    if (qrfilename is None) or (not re_qrfilename.match(qrfilename)):
        flash("QR code filename format is invalid")
        return redirect("/home_ahc")
    else:
        qrc = qrfilename.split("_")
        if unixtime_int() > int(qrc[0]):      # The QR code has expired so
            os.unlink(QR_CODES + qrfilename)    # the PNG file is deleted.
            flash("The QR code has expired")
            return redirect("/home_ahc")

    qr_png_path = QR_CODES + qrfilename

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "create_currency"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

    primid_fph, primid_hrns, etypes, \
    m = identify_entity(current_user.get_id())

    working_identity_type = "primid"
    if (hub_mode != "slate") and ("working_identity" in session):
        working_identity_fph, working_identity_hrns, etypes, \
        m = identify_entity(session["working_identity"])
    else:
        working_identity_fph = primid_fph
        session["working_identity"] = working_identity_fph
        working_identity_hrns = primid_hrns
        working_identity_type = etype_to_adtype(working_identity_fph)

    number_of_messages, \
    number_of_indelible_messages = message_count(primid_fph, hub_mode)

    return render_template(
        "display_invitation_qr.html",
        title = "Display invitation QR code",
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        logged_in = logged_in,
        primid_type = "login identity",
        primid_fph = primid_fph,
        primid_hrns = primid_hrns,
        working_identity_fph = working_identity_fph,
        working_identity_hrns = working_identity_hrns,
        working_identity_type = working_identity_type,
        number_of_messages = number_of_messages,
        number_of_indelible_messages = number_of_indelible_messages,
        qrfilename = qrfilename
    )

# help ========================================================================

@app.route("/help")
def help():
    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    page = "help"
    group = "help"
    namespace_steward = True
    currency_steward = True
    paying = False

    logged_in = current_user.is_authenticated

    # If the user is not logged in, a basic summary is shown.
    if not logged_in:
        help_page = "unspecific"
    elif "previous_page" in session:
        help_page = session["previous_page"]

    # Otherwise, contextual help is shown detemined by the previous page (from
    # which help was requested). That previous page is also where control must
    # be returned after the help page has been read.
    #
    # If help is invoked from one of the contextual help pages, control is
    # returned to the previous page.

    return render_template(
        "help.html",
        title = "help",
        help_page = help_page,  # Determines which template section to use.
        logged_in = logged_in,
        page = page,
        group = group,
        hub_mode = "slate",
        version = get_version(),
        show_csv_import_link = get_config("show_dataset_csv_import_link"),
        development_mode = development_mode,
        namespace_steward = namespace_steward,
        currency_steward = currency_steward
    )

@app.route("/back")
def back():
    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()
    page = "back"
    group = "help"
    logged_in = current_user.is_authenticated
    # If the user is not logged in, a basic summary is shown.
    if not logged_in:
        return redirect("/")
    elif "previous_page" in session:
        primid_fph, primid_hrns, etypes, \
        m = identify_entity(current_user.get_id())

        help_page = session["previous_page"]
        if help_page == "home_ahc":
            return redirect("/home_ahc")
        elif help_page == "create_namespace":
            return redirect("/create_namespace")
        elif help_page == "create_currency":
            return redirect("/create_currency")
        elif help_page == "create_pairing":
            return redirect("/create_pairing/" + primid_fph)
        elif help_page == "import_dataset":
            return redirect("/import/dataset")
        elif help_page == "invitation_generate":
            return redirect("/invitation/generate")
        else:
            return redirect("/home_ahc")
