import os
import json
from pathlib import Path
import sys
import pickle

import bcrypt
from itsdangerous import URLSafeTimedSerializer

## SLATE components: -----------------------------------------------------------

from app.core.constants import NSS
#from app.core.constants import SLATE_EXPORT, SLATE_IMPORT

from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.fph_hrns_maps import hrns_exists_already

from app.core.slate_core import get_entity_type, get_account_currency
from app.core.slate_core import identify_entity, get_primid
from app.core.slate_core import new_primid, new_secid
from app.core.slate_core import update_primid_access_details
from app.core.slate_core import new_namespace, new_currency
from app.core.slate_core import new_account
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

from app.core.slate_session import create_slate_session_db
from app.core.slate_session import session_save_currencies_available
#from app.core.slate_session import retrieve_currency_options
from app.core.slate_session import session_retrieve_payment_options
from app.core.slate_session import session_save_payee_accounts_available
from app.core.slate_session import session_retrieve_payee_accounts_available

from app.core.regexp_list import re_fph, re_hrns, re_email

from app.core.slate_login import get_auth_data, register_authenticated_login

##from app.core.auth import pin_random_ord, pin_prompt_message
from app.core.auth import pin_subset_prompt
from app.core.auth import check_auth_hash, authenticate_pin

from app.core.logging import log_event

from app.core.payments import payment
#from app.core.payments import dump_account_payments
from app.core.exports import list_payments_for_account
from app.core.exports import dump_account_payments_csv
from app.core.exports import list_payments_in_currency
from app.core.exports import dump_currency_payments_csv

from app.core.uploads import csv_create_namespaces
from app.core.uploads import csv_create_identities
from app.core.uploads import csv_create_currencies
from app.core.uploads import csv_create_accounts

from app.core.messaging import display_colour_subject_prefix
from app.core.messaging import create_hubs_db
from app.core.messaging import send_message
from app.core.messaging import fetch_messages

from app.core.mail_temp import temp_mail_send

from app.core.display import yesno, integer_to_money_format
from app.core.display import etype_to_adtype

from app.core.csv_import import import_minimal_payment_set_as_csv

from app.site_configuration import site_config

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
from app.forms import PaymentToAccountForm, PaymentToIdentityForm
from app.forms import CurrencyCreateForm
from app.forms import AccountCreateForm
from app.forms import NamespaceCreateForm
from app.forms import SecidCreateForm
from app.forms import SpecifyPayeeAccountForm
from app.forms import SpecifyPayeeAgentForm
from app.forms import StewardAddForm
#from app.forms import TQueueForm
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
#        flash(
#            "Registration submitted for user {}".format(
#                # The username captured here is not the same as the login
#                # identity which comprises: username.namespace (parent)
#                form.username.data,
#                form.namespace.data,
#                form.realname.data,
#                form.currency.data,
#                form.email_1.data,
#                form.email_2.data,
#                form.password.data,
#                form.password_repeat.data,
#                form.pin.data
#            )
#        )
        # At this point the initial *currency* may have been specified in
        # either the URL or the form. If the *currency* FPH was specified in
        # the URL, the *currency* HRNS field will not have been displayed.

#        currency_identifier = form.currency.data  # (from the form)
        currency_identifier = form.currency.data.strip()  # (from the form)
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
        namespace_identifier = form.namespace.data.strip().lstrip(".")
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
        if etype != "namespace":
            flash(namespace_identifier + " is not a namespace")
            return redirect("/register")
        # If control reaches this point then *namespace* (whether specified
        # in the form or in the URL) exists.

        if form.password_repeat.data !=  form.password.data:
            flash("The passwords not not match")
            return redirect("/register")

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
            flash("The primid cannot be created. See error log.")
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

        session["previous_page"] = "home"           # (This one subsequently
                                                    # serves as shift register).

        return redirect(url_for("home"))

    return render_template(
                "login.html",
                title = "Sign in",
                page = page,
                mode = mode,           # ???
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
                mode = mode
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
               form = form
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

# ==============================================================================
# login landing page

@app.route("/home/new", methods = ["GET", "POST"])
@login_required
def new_home():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "new_home"
    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
#        session["previous_page"] = "home" ### probably not needed
        previous_page = "home"
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    hub_mode = get_hub_mode() ### New variable added

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









## NB: This will be assigned a new endpoint to allow "/home" to be used for a
##     sparser login landing page centred around internal messaging.

@app.route("/home/full", methods = ["GET", "POST"])
@app.route("/home", methods = ["GET", "POST"])
@login_required
def home():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "home"
    if "previous_page" in session: # already active
        previous_page = session["previous_page"]
    else: # initializing
#        session["previous_page"] = "home" ### probably not needed
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
            account_balance, \
            m = get_account_specific_properties(account_fph)

            # Fetch currency details:
            currency_fph, \
            currency_hrns, \
            prefix, \
            suffix, \
            default_account_name, \
            stewards_list, \
            m = get_currency_specific_properties(account_currency_fph)


            print(
                fph_to_hrns(account_fph) + " (" \
                + fph_to_hrns(account_owner_fph) + ") [" \
                + currency_hrns + "] :: " \
                + integer_to_money_format(account_balance)
            )


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

# ==============================================================================
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
            a_balance, \
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
                primary_identity_type = "login identity",
                primary_identity_fph = primary_identity_fph,
                primary_identity_hrns = primary_identity_hrns,
                working_identity_fph = working_identity_fph,
                working_identity_hrns = working_identity_hrns,
                working_identity_type = working_identity_type,
                # List of *currencies* available:
                currencies_list = currencies_list
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

#    print("currency_fph passed in URL is " + currency_fph)

    hub_mode = get_hub_mode()   # This is read from an environment variable
                                # configured at installation time.

    page = "payment_options"
    previous_page = session["previous_page"]
    session["previous_page"] = page

    group = "home" # Used to control top menu behaviour.

    currencies_available, payment_options_list, m = session_retrieve_payment_options()
    if m == "Payment options unavailable":
        return redirect("/currency/options")

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

@app.route("/account/<payer_account_fph>/<payee_account_fph>",
           methods = ["GET", "POST"])
@login_required
def account(payer_account_fph, payee_account_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "account"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
    group = "home" # Used to control top menu behaviour.

    logged_in = current_user.is_authenticated

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
        if payee_account_fph == "00000000000000000000000000000000":
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
    payer_balance, \
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
        payee_balance, \
        m = get_account_specific_properties(payee_account_fph)

        if payee_currency_fph !=  payer_currency_fph:
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
            return redirect("/account/" + payer_account_fph)

        payer_currency_fph, \
        payer_owner_fph, \
        payer_balance, \
        m = get_account_specific_properties(payer_account_fph)

        payee_currency_fph, \
        payee_owner_fph, \
        payee_balance, \
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
                primary_identity_type = "login identity",
                primary_identity_fph = primary_identity_fph,
                primary_identity_hrns = primary_identity_hrns,
                working_identity_fph = working_identity_fph,
                working_identity_hrns = working_identity_hrns,
                working_identity_type = working_identity_type,
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
@app.route("/pay_to_account", methods = ["GET", "POST"])
@login_required
def pay_account():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "pay_account"
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
                primary_identity_type = "login identity",
                primary_identity_fph = primary_identity_fph,
                primary_identity_hrns = primary_identity_hrns,
                working_identity_fph = working_identity_fph,
                working_identity_hrns = working_identity_hrns,
                working_identity_type = working_identity_type
           )

#=============================================================================
# Make a payment to an *agent* rather than to an *account*.
#
@app.route(
    "/pay/agent/", methods = ["GET", "POST"]
)
@app.route(
    "/pay/agent/<payer_account_fph>", methods = ["GET", "POST"]
)
@app.route(
    "/pay/agent/<payer_account_fph>/<currency_fph>", methods = ["GET", "POST"]
)
@app.route(
    "/pay/agent/<payer_account_fph>/<currency_fph>/<selected_account_fph>",
    methods = ["GET", "POST"]
)
@login_required
def pay_agent(
        payer_account_fph=None,
        currency_fph=None,
        selected_account_fph=None
    ):
    # The *currency* is identified from the payer *account* passed in the URL
    # slug. The payee will have specified an *identity* and a *currency*, both
    # of which are entered into the form below, so here we need only verify
    # that payer also has an *account* in this *currency*. If control has been
    # passed to this screen from the "/currency/options" endpoint, then the
    # availability of the *currency* to the payer will have been established
    # already. Otherwise it will be necessary to establish that from the payer
    # *account*.
    currency_fph = ""
    if payer_account_fph is not None:
        if re_fph.match(payer_account_fph):
            currency_fph = get_account_currency(payer_account_fph)
            currency_hrns = fph_to_hrns(currency_fph)
    else:
        flash("No payer account specified")
        return redirect("/home")

    if selected_account_fph is not None:
        if not re_fph.match(selected_account_fph):
            flash("Invalid FPH for selected account")
            return redirect("/home")
        payee_currency = get_account_currency(selected_account_fph)
        if payee_currency != currency_fph:           # This should never happen
            flash("Account currencies do not match") # happen unless URL has
            return redirect("/home")                 # constructed externally.
    else:
        selected_account_fph = ""

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "pay_agent"
    group = "home"
    logged_in = current_user.is_authenticated

    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
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

    form = SpecifyPayeeAgentForm()
    if form.validate_on_submit():
        payee_identity_fph, \
        payee_identity_hrns, \
        etype, \
        m = identify_entity(form.to_identity_id.data) # HRNS or FPH
        if m:
            flash(m)
            return redirect("/pay/agent")
        if payee_identity_fph == "": # *agent* cannot be identified
            return redirect("/pay/agent")

        currency_fph, \
        currency__hrns, \
        etype, \
        m = identify_entity(form.currency_id.data)
        if m:
            flash(m)
            return redirect("/pay/agent")
        if currency_fph == "": # *currency* cannot be identified
            return redirect("/pay/agent")

        amount = form.amount.data

        annotation = form.annotation.data

        # Now we need to find an *account* in the specified *currency*
        # belonging to the specified payee *identity*.

        payee_accounts, m = list_agent_accounts(payee_identity_fph)
        payable_accounts = []
        for payee_account_fph in payee_accounts:
            account_currency_fph = get_account_currency(payee_account_fph)
            if account_currency_fph == currency_fph:
                payable_accounts.append(account_currency_fph)

        # If there is only one payable *account*, the payment can be made
        # immediately. Otherwise the list of payable *accounts* in this
        # *currency* must be passed on to another endpoint to allow the payer
        # to make a selection.

        if len(payable_accounts) == 0:
            flash("The payee has no accounts in the specified currency")
            return redirect("/pay/agent")
        elif len(payable_accounts) == 1:
            m = payment(
                    payer_account_fph,
                    payee_account_fph,
                    amount,
                    annotation
                )
            if m:
                flash(m)
            else:
                flash("Payment made to " + fph_to_hrns(payee_account_fph))
                return redirect("/home")
            return redirect("/pay/agent")
        elif selected_account_fph:
            m = payment(
                    payer_account_fph,
                    selected_account_fph,
                    amount,
                    annotation
                )
            if m:
                flash(m)
                return redirect("/pay/agent")
            else:
                flash("Payment made to " + fph_to_hrns(selected_account_fph))
                return redirect("/home")
        else:
            # Control reaches this point only if the *payee* has more than one
            # *account* in the specified *currency*.
#            many_payee_account_options = True

            payee_account_options = []
            for payee_account_fph in payable_accounts:
                a = {}
                a["fph"] = payee_account_fph
                a["hrns"] = fph_to_hrns(payee_account_fph)
                payee_account_options.append()
            session_save_payee_accounts_available(payable_accounts)
            return redirect(
                       "/pay/agent/" + payer_account_fph + "/" + currency_fph
                   )


    return render_template(
                "pay_to_agent.html",
                title = "Make a payment to an agent",
                page = page,
                group = group,
                form = form,
                logged_in = logged_in,
                hub_mode = hub_mode,
                currency_fph = currency_fph,
                currency_hrns = currency_hrns,
                primary_identity_type = "login identity",
                primary_identity_fph = primary_identity_fph,
                primary_identity_hrns = primary_identity_hrns,
                working_identity_fph = working_identity_fph,
                working_identity_hrns = working_identity_hrns,
                working_identity_type = working_identity_type
#                many_payee_account_options = many_payee_account_options,
#               payable_accounts = payable_accounts
           )

# Select from available payee accounts
#
@app.route("/pay/agent/accounts/<payer_account_fph>/<currency_fph>",
           methods = ["GET", "POST"])
@login_required
def select_account_to_which_to_pay(payer_account_fph, currency_fph ):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "select_account_combination_in_currency"
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

    # Control reaches this point only if the *payee* has more than one
    # *account* in the specified *currency*.

    payee_accounts_available, m = session_retrieve_payee_accounts_available()
    payee_account_options = []
    for payee_account_fph in payee_accounts_available:
        a = {}
        a["fph"] = payee_account_fph
        a["hrns"] = fph_to_hrns(payee_account_fph)
        payee_account_options.append()



    return render_template(
                "payee_account_options.html",
                title = "Make a payment to a selected account",
                page = page,
                group = group,
                form = form,
                logged_in = logged_in,
                hub_mode = hub_mode,
                currency_fph = currency_fph,
                currency_hrns = currency_hrns,
                primary_identity_type = "login identity",
                primary_identity_fph = primary_identity_fph,
                primary_identity_hrns = primary_identity_hrns,
                working_identity_fph = working_identity_fph,
                working_identity_hrns = working_identity_hrns,
                working_identity_type = working_identity_type,
                payee_account_options = payee_account_options
           )





# payment to an *agent* -- select available payer-payee *account* pair --------
@app.route("/select_account_combination_in_currency" \
           + "/<payee_identity_fph>/<currency_fph>", methods = ["GET", "POST"])
@login_required
def select_account_combination_in_currency(payee_identity_fph, currency_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "select_account_combination_in_currency"
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
def select_payer_account(payee_account_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

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
    payee_account_balance, \
    m = get_account_specific_properties(payee_account_fph)

    number_of_payer_accounts = 0
    payer_usable_accounts = []
    payer_accounts_list, m = list_agent_accounts(identity_fph)

    for account_fph in payer_accounts_list:

        account_currency_fph, \
        account_owner_fph, \
        account_balance, \
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
    account_balance, \
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
                "manage_secids.html",
                title = "Manage an alias",
                page = page,
                group = group,
                hub_mode = hub_mode,
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







# MANAGEMENT ==================================================================

# management ------------------------------------------------------------------
@app.route("/manage", methods = ["GET", "POST"])
@login_required
def manage():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

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
        m = identify_entity(form.namespace_id.data)
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
            + currency_hrns + " [" + currency_fph + "]"
        )
        return redirect("/create_currency")
        #return redirect("/home")

    return render_template(
                "create_currency.html",
                title = "Create a currency",
                logged_in = logged_in,
                page = page,
                group = group,
                hub_mode = hub_mode,
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

# create an account -----------------------------------------------------------
@app.route("/create_account/<owner_fph>", methods = ["GET", "POST"])
@login_required
def create_account(owner_fph):

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "create_account"
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

    form = AccountCreateForm()
    if form.validate_on_submit():
        namespace_fph, \
        namespace_hrns, \
        etype, \
        m = identify_entity(form.namespace_id.data) # parent *namespace*
        if m:
            flash(m)
            #return redirect("/create_account")
            return redirect("/home")
        if not namespace_fph:
            flash("Parent namespace does not exist")
            #return redirect("/create_account")
            return redirect("/home")

        account_name = form.account_name.data
        # Check whether an entity with the proposed HRNS exists already.
        proposed_hrns = account_name + "." + namespace_hrns
        if hrns_exists_already(proposed_hrns):
            flash(proposed_hrns + " is already registered")
            return redirect("/home")
            #return redirect("/create_account")

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
            #return redirect("/create_account")
            return redirect("/home")

        account_fph, \
        account_hrns, \
        m = new_account(
                account_name,
                namespace_fph,
                owner_fph, # the owner of this *account*
                currency_fph
            )
        if m:
            flash(m)
        flash(
            "A new account has been created, identified as \n" \
            + account_hrns + " [" + account_fph + "]"
        )
        #return redirect("/create_account")
        return redirect("/home")

    return render_template(
                "create_account.html",
                title = "Create an account",
                logged_in = logged_in,
                page = page,
                group = group,
                hub_mode = hub_mode,
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

    page = "list_identities"
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

    group = "home" # Used to control top menu behaviour.
    page = "create_secid"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.

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
        m = identify_entity(form.parent_namespace_id.data) # parent *namesapce*
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
            + secid_hrns + " [" + secid_fph + "]"
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
        #return redirect("/home")

    return render_template(
                "create_secid.html",
                title = "Create an alias",
                logged_in = logged_in,
                page = page,
                group = group,
                hub_mode = hub_mode,
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

    page = "create_namespace"
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

    #user = User(identity_fph) # Retrieve the user object
    #primary_identity_fph = current_user.get_id()
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
        m = identify_entity(form.parent_namespace_id.data) # parent *namesapce*
        if m:
            flash(m)
            return redirect("/create_namespace")
        if not parent_namespace_fph:
            flash("Parent namespace does not exist")
            return redirect("/create_namespace")

        default_currency_fph = get_default_currency_fph(parent_namespace_fph)

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
                primary_identity_fph # the initial steward of this new *namespace*
            )
        flash(
            "A new namespace has been created, identified as \n" \
            + namespace_hrns + " [" + namespace_fph + "]"
        )
        return redirect("/create_namespace")
        #return redirect("/home")

    return render_template(
                "create_namespace.html",
                title = "Create a namespace",
                logged_in = logged_in,
                page = page,
                group = group,
                hub_mode = hub_mode,
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

    page = "list_namespaces"
    previous_page = session["previous_page"]    # Add these two lines to all
    session["previous_page"] = page             # endpoint handlers. Some (but
                                                # but by no means all) screens
                                                # should be able to follow only
                                                # from a limited set of previous
                                                # screens.
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
#        print(namespace)
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
                primary_identity_type = "login identity",
                primary_identity_fph = primary_identity_fph,
                primary_identity_hrns = primary_identity_hrns,
                available_namespaces = available_namespaces
           )

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

@app.route("/import/payments_set")
@login_required
def import_payments_set():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

    page = "sandbox_payment_set_import"
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


    import_minimal_payment_set_as_csv(
        owner_identifier,
        currency_identifier,
        namespace_identifier,
        csv_file_path
    )



    return


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
        namespace_active, \
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

    page = "export_account"
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
    balance, \
    m = get_account_specific_properties(account_fph)
    if m:
        flash(m)
        return redirect("/home")

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
               #csv_export_path = csv_export_path
               csv_file = csv_file
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
##

@app.route('/uploads/<filename>')
@login_required
def upload(filename):
    return send_from_directory(os.path.join(
        app.config["UPLOAD_PATH"], current_user.get_id()), filename)





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






# help ========================================================================
@app.route("/help")
def help():

    # Hub operational mode (read from environment variable HUB_MODE)
    hub_mode = get_hub_mode()

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
                development_mode = development_mode,
                namespace_steward = namespace_steward,
                currency_steward = currency_steward
           )
