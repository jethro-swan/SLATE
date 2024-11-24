import os
import json
from pathlib import Path
import sys

import bcrypt

#from flask_bcrypt import Bcrypt # 2024-11-10: Try this out to resolve problem
#                                # with check_auth_hash( )
#                                # ("ValueError: Invalid salt")

# SLATE components: -----------------------------------------------------------

from app.core.constants import NSS
from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.slate_core import get_entity_type, get_account_currency
from app.core.slate_core import identify_entity, get_primid
from app.core.slate_core import new_primid
from app.core.slate_core import list_stewardships, list_stewards
from app.core.slate_core import retrieve_primid_access_details
from app.core.slate_core import list_agent_accounts, list_secids
from app.core.slate_core import get_currency_specific_properties
from app.core.slate_core import get_account_specific_properties
from app.core.regexp_list import re_fph, re_hrns, re_email
from app.core.slate_login import get_auth_data, register_authenticated_login
##from app.core.auth import pin_random_ord, pin_prompt_message
from app.core.auth import pin_subset_prompt
from app.core.auth import check_auth_hash, authenticate_pin
from app.core.logging import log_event
from app.core.payments import payment

from app.core.display import yesno, integer_to_money_format



#from app import bcrypt # added 2024-11-10

#, authenticate_web_access
#from app.core.auth import set_web_password_hash


# Flask components: -----------------------------------------------------------

from flask import render_template, flash, redirect, url_for
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_login import login_required
from flask import session, g, request
from app import app
from app.models import User
from app.forms import LoginForm, RegistrationForm, LoginRecoveryForm
from app.forms import PaymentToAccountForm, PaymentToIdentityForm
#from app.forms import PaymentToAccountHRNSForm, PaymentToIdentityHRNSForm
#from app.forms import PaymentToAccountFPHForm, PaymentToIdentityFPHForm
from app.forms import CurrencyCreateForm
from app.forms import TQueueForm
from markupsafe import escape

#------------------------------------------------------------------------------
# Shared local functions:

# Create the identity type display string:
def fph_to_display_type(agent_identifier):
    agent_fph, \
    agent_hrns, \
    etype, \
    m = identify_entity(agent_identifier)
    if etype == "primid":
        return "primary identity"
    elif etype == "secid":
        return "secondary identity"
    else:
        return ""

# The *primid* need only be displayed if the current active identity is a
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
@app.route("/register", methods=["GET", "POST"])
def register():
    page = "register"
    # In a typical situation where the new user is invited (via QR-coded link)
    # to register, it is likely that both the currency and a geographically
    # appropriate user namespace will be specified. However, that will not
    # necessarily always be the case. Since neither, either or both may be
    # provided in the invitation link, the request.args variable is used
    # instead so the route may look like any of the following:
    #   /register
    #   /register?c_fph=0c75584102039b93
    #   /register?c_fph=0c75584102039b93&ns_fph=95a5467fed65bbac
    #   /register?ns_fph=95a5467fed65bbac

    # The following variables are used to determine which menu subsets are
    # displayed:
    page = "registration"
    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    # This one may not be needed:
    mode = "logged_out"

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
    if not (initial_currency_fph and (etype == "currency")):
        initial_currency_fph = ""
        initial_currency_hrns = ""

    initial_namespace_identifier = request.args.get("ns_fph")
    initial_namespace_fph, \
    initial_namespace_hrns, \
    etype, \
    m = identify_entity(initial_namespace_identifier)
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
        flash(
            "Registration submitted for user {}".format(
                # The username captured here is not the same as the login
                # identity which comprises: username.namespace (parent)
                form.username.data,
                form.namespace.data,
                form.realname.data,
                form.currency.data,
                form.email_1.data,
                form.email_2.data,
                form.password.data,
                form.password_repeat.data,
                form.pin.data
            )
        )
        # At this point the initial *currency* may have been specified in
        # either the URL or the form. If the *currency* FPH was specified in
        # the URL, the *currency* HRNS field will not have been displayed.

        currency_identifier = form.currency.data  # (from the form)
        # The identify_entity( ) function determines whether either is valid.
        currency_fph, \
        currency_hrns, \
        etype, \
        m = identify_entity(currency_identifier)
        if m:
            log_event("error", "currency", m)
            flash("Unknown error (logged)")
            redirect("/register")
        if not currency_fph:
            flash("No valid currency identifier provided")
            redirect("/register")
        if etype != "currency":
            flash(currency_identifier + " is not a currency")
            redirect("/register")

        # Similarly, at this point the parent *namespace* may have been
        # specified in either the URL or the form. If the parent *namespace*
        # FPH was specified in the URL, the *currency* HRNS field will not have
        # been displayed.

        namespace_identifier = form.namespace.data
        # The identify_entity( ) function determines whether either is valid.
        namespace_fph, \
        namespace_hrns, \
        etype, \
        m = identify_entity(namespace_identifier)
        if m:
            log_event("error", "namespace", m)
            flash("Unknown error (logged)")
            redirect("/register")
        if not namespace_fph:
            flash(namespace_identifier + " does not exist")
            redirect("/register")
        if etype != "namespace":
            flash(namespace_identifier + " is not a namespace")
            redirect("/register")
        # If control reaches this point then *namespace* (whether specified
        # in the form or in the URL) exists.

        if form.password_repeat.data != form.password.data:
            flash("The passwords not not match")
            redirect("/register")

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
        else:
            flash(primid_hrns + " [" + primid_fph + "] has been registered")
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
                title="User registration",
                form=form,
                logged_in=logged_in,
                page=page,
                mode=mode,
                development_mode=development_mode,
                initial_namespace_fph=initial_namespace_fph,
                initial_namespace_hrns=initial_namespace_hrns,
                initial_currency_fph=initial_currency_fph,
                initial_currency_hrns=initial_currency_hrns,
                namespace_steward=False,
                currency_steward=False
           )

# login -----------------------------------------------------------------------
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    page = "login" # Variable used to identify which menu items to display.
    mode = "logged_out"
    logged_in = False
    if current_user.is_authenticated: # user is already logged in
        mode = "logged_in"
        logged_in = True
        return redirect(url_for("home"))

    #form = LoginForm(pro=pro, pin_prompt=pin_prompt)
    form = LoginForm()
    if form.validate_on_submit():

        agent_identifier = form.identity.data # HRNS or FPH
        identity_email = form.email.data

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
            if (etype != "primid") and (etype != "secid"):
                flash("Invalid identity entered")
                return redirect(url_for("login"))
            if etype == "secid": # authentication requires primary *identity*
                identity_fph, m = get_primid(identity_fph)
                if m:
                    flash(m)
                    log_event(
                        "errors", "primid entification",
                        "The primid cannot be identified from " + identity_fph
                    )
                    return redirect(url_for("login"))
            if identity_fph:
                # If control reaches this point and the FPH exists, we have a
                # valid *primid* for the HRNS or FPH entered.
#                flash(
#                    identity_hrns + " = [" + identity_fph + "] has " \
#                    + "been identified from the agent identifier."
#                )
                primid_has_been_identified_from_identity = True
            else:
                flash(identity_fph + " is not a registered identity.")

        elif identity_email:
            if not re_email.match(identity_email):
                flash("The email address is invalid.")
                return redirect(url_for("login"))
            else:
                identity_fph_from_email = email_to_primid(identity_email)
                # Returns "" if the email address not mapped to *primid* FPH.
                if not identity_fph_from_email:
                    flash("This email address is not registered here.")
                    return redirect(url_for("login"))
                else:
                    primid_has_been_identified_from_email = True
                    if primid_has_been_identified_from_identity:
                        if primid_identified_from_email != identity_fph:
                            flash(
                                "The email address provided here is not " \
                                + "consistent with the user identity " \
                                + "already validated."
                            )
                            return redirect(url_for("login"))
                    else:
                        identity_fph = identity_fph_from_email
                        identity_hrns = fph_to_hrns(identity_fph)
                        flash(
                            identity_hrns + " = [" + identity_fph + "] has " \
                            + "been identified from the email address."
                        )

        else:
            flash("No valid identifier has been provided.")
            return redirect(url_for("login"))


        # If control reaches this point, we have a valid *identity* (which may
        # be a *primid* or a *secid*) for the email address entered.
        #
        # Alternatively, the *primid*
        # Whether from the agent field (*primid*|*secid*) or from an email
        # address, we have now identified the *primid*.
        print("identity = " + identity_fph + " = [" + identity_hrns + "]")

        password_hash, \
        stored_pin, \
        access_token_hash, \
        m = get_auth_data(identity_fph)
        if m:
            flash(m)
            return redirect(url_for("login"))

        print("password hash = " + password_hash)
        print("PIN = " + stored_pin)
        print("access_token_hash = " + access_token_hash)

        # Retrieve the user object:
        user = User(identity_fph)

        password = form.password.data
        print("form.password.data = " + form.password.data)
        password2 = form.password.data.strip()
        print("password strip()ped = " + form.password.data)
        if password != password2:
            print("password corrupted")

#        if not check_auth_hash(password_hash, form.password.data):
#            flash("Password check failed ... but you can come in anyway")

        pwd = password
        pwd_hash = password_hash
        if not bcrypt.checkpw(pwd.encode("utf-8"), pwd_hash.encode("utf-8")):
            #flash("Password check failed ... but you can come in anyway")
            return redirect(url_for("login"))
        #else:
            #flash("Password check successful")

        if not authenticate_pin(stored_pin, form.pse.data, form.pro.data):
            flash("Incorrect PIN digits")
            return redirect(url_for("login"))

        # Register the authenticated login:
        register_authenticated_login(identity_fph)

        login_user(user, remember=form.remember_me.data)

        return redirect(url_for("home"))

    return render_template(
                "login.html",
                title="Sign in",
                page=page,
                mode=mode,           # ???
                logged_in=logged_in, # ???
                form=form,
                development_mode=development_mode
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



# login recovery --------------------------------------------------------------
@app.route("/login/recover", methods=["GET", "POST"])
def login_recover():
    page = "login_recovery"
    mode = "logged_out"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated
    form = LoginRecoveryForm()
    if form.validate_on_submit():
        flash(
            "Recovery details submitted for user {}".format(
                form.identity.data,
                form.fph.data,
                form.email.data
            )
        )
        identity_hrns = form.identity.data  # Get rid of these and replace with
        identity_fph = form.fph.data        # agent_identifier (HRNS or FPH)
        identity_email = form.email.data

        # (Most of the following chunk of code has been re-used from /login so
        # it may be possible to factorize this in due course.)
        if (identity_hrns == "") and (identity_fph == ""): # neither provided
            flash("Either an HRNS on an FPH must be provided for identity.")
            return redirect(url_for("login"))
        if identity_hrns:
            if not re_hrns.match(identity_hrns):
                flash("The identity is invalid.")
                return redirect(url_for("login"))
            else:
                identity_fph = hrns_to_fph(identity_hrns)
        elif identity_fph:
            if not re_fph.match(identity_fph):
                flash("The identity FPH is invalid.")
                return redirect(url_for("login"))
        # At this point, whether derived from the HRNS or entered directly as
        # an FPH, we have something that looks like an FPH. It must now be
        # determind whether this actually represents a registered identity.
        entity_fph, \
        entity_hrns, \
        etype, \
        m = identify_entity(agent_identifier)

        # m = identify_entity(identity_fph)   # This should be agent_identifier,
                                            # so change it ...
        # If control has recahed this point, this is a registered entity of
        # some type, but is it a *primid*?
        if etype != "primid":
            flash(agent_identifier + " is not a primary identity.")
            return redirect(url_for("login"))
        # If control reaches this point, the entity identifier entered has been
        # identified as a registered *primid*.
        if not identity_email:
            flash("Login recovery is not possible without an email address.")
            return redirect(url_for("login"))
        elif not re_email.match(identity_email):
            flash("The email address is invalid.")
            return redirect(url_for("login"))
        else:
            identity_fph_2 = email_to_primid(identity_email)
            # Returns "" if the email address is not mapped to a *primid*.
            if not identity_fph_2:
                flash("This email is not registered here.")
                return redirect(url_for("login"))
        # If control reaches this point, we have a valid email address for the
        # identity entered.

# At this point we need to ...
# (1) Generate a random recovery token string;
# (2) hash that string using xxHash128;
# (3) assemble a URL comprising: address of recovery form + recovery token
#     e.g. https://locus1.lrc.org.uk?rt=c32ad8d181e8807a54282e817dabe328
# (4) generate a time limit (e.g. 20 minutes, to accommodate slow email
#     delivery) and add that to the current Unix timestamp to create a deadline
#     value;
# (5) Register that token as the key in a recovery dictionary with the deadline
#     as the value;
# (6) flash a message to the user explaining that an email has been sent
#     containg a time-limited recovery link; and
# (7) assemble and send the recovery email.
#
# When the using clicks on the recovery link, it is taken to the recovery form
# to enter a new password and PIN. (This for can probably be constructed from
# parts of the /register form).
#
# NB, for (2), use of auth_hash() to take advantage of Bcrypt's salt feature,
# would make it more challenging to create a "web safe" URL string and is
# probably not worth the trouble.

        return redirect("/login")

    return render_template(
                "login_recovery.html",
                title="Login recovery",

                #logged_in=logged_in,
                #page=page,
#                group=group,
                identity_type=etype,
#                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,


                form=form,
                logged_in=logged_in,
                page=page,
                mode=mode,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# login landing page ----------------------------------------------------------
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    page = "home"
    group = "home"

    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id() # *primid* as which logged in
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    # The user logs in as the *primid*, even if indirectly as one of its
    # *secid*s, but once logged in will see all of its *identities* along with
    # a list of *accounts* belonging to each. The user will also see a list of
    # entities over which it holds/shares stewardship.

    stewardships_list, m = list_stewardships(identity_fph)

    print("Currently in the /home endpoint")
    print("identity_fph = " + identity_fph)
    print("identity_hrns = " + identity_hrns)
    print("identity_type = " + identity_type)

    # Since a user may have *accounts* scattered across an arbitrary number of
    # *namespaces*, it is necessary to maintain a list of these:

    # A full list of *identities* is compiled, with the *primid* first:
    identities_list = list_secids(identity_fph)
    identities_list.insert(0, identity_fph)

    identities = [] # list of *identities* to pass to "home.html" template as
                    # dictionaries.

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
            id["type"] = "primary identity"
        elif etype == "secid":
            id["type"] = "secondary identity"
        else:
            etype == "poltergeist" # something to be investigate

        accounts_list, m = list_agent_accounts(id_fph)
        if m:
            flash(m)

        # List the *accounts* belonging to this *identity*:
        accounts = [] # (second-level dictionary for iteration in template)
        #accounts = {} # (second-level dictionary for iteration in template)
        for account_fph in accounts_list:
            # Fetch account details:
            account_currency_fph, \
            account_owner_fph, \
            account_balance, \
            m = get_account_specific_properties(account_fph)

            print("account_currency_fph  \t= " + account_currency_fph)
            print("account_owner_fph  \t= " + account_owner_fph)
            print("account_balance  \t= " + str(account_balance))

            # Fetch currency details:
            currency_fph, \
            currency_hrns, \
            prefix, \
            suffix, \
            stewards_list, \
            m = get_currency_specific_properties(account_currency_fph)

            print("currency_fph  \t= " + currency_fph)
            print("currency_hrns  \t= " + currency_hrns)
            print("stewards_list  \t= ", end="")
            print(stewards_list)

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
            primid_currency_steward = currency_fph in stewardships_list
            a["primid_is_currency_steward"] = primid_currency_steward
            #if currency_fph in stewardships_list:
            #    a["primid_is_currency_steward"] = True
            #else:
            #    a["primid_is_currency_steward"] = False
            a["currency_fph"] = currency_fph
            a["currency_hrns"] = currency_hrns

            print("a  \t= ", end="")
            print(a)

            #accounts[account_fph] = a
            accounts.append(a)

        id["accounts"] = accounts
        identities.append(id)


    # If this is a *primid*, fetch a list of its *secid*s and stewardships:
    secid_list = list_secids(identity_fph)
    secids = []
    print("secids for " + fph_to_hrns(identity_fph))
    for secid_fph in secid_list:
        if secid_fph != "":
            print(identity_fph + " :: " + fph_to_hrns(secid_fph))
            secid = {}
            secid["fph"] = secid_fph
            secid["hrns"] = fph_to_hrns(secid_fph)
            secids.append(secid)

    #stewardships_list, m = list_stewardships(identity_fph)
    stewardships = []
    print("stewardships for " + fph_to_hrns(identity_fph))
    for stewardship_fph in stewardships_list:
        if stewardship_fph != "":
            print(identity_fph + " :: " + fph_to_hrns(stewardship_fph))
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
                title="Home",
                page=page,
                group=group,
                development_mode=development_mode,
                logged_in=logged_in,
                #namespace_steward=namespace_steward,
                #currency_steward=currency_steward,

                # Variables passed for display in "base.html":
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,

                # List of (nested) dictionaries for display in "home.html":
                identities=identities,
                #accounts=accounts,
                secids=secids,
                stewardships=stewardships
            )

# account details page --------------------------------------------------------
@app.route("/account/<account_fph>", methods=["GET", "POST"])
@login_required
def account(account_fph):
#def account(account_fph=None):
    page = "account"
    group = "home"
    #mode = ""
#    namespace_steward = False  ## ???
#    currency_steward = False   ## ???
    paying = False
    logged_in = current_user.is_authenticated

    # The *primid* (or its alias *secid*) logged in currently:
    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)

    # (This uses the identify_entity( ) function:)
    identity_type = fph_to_display_type(identity_fph)

    # If an *account* has been specified (by FPH) in the URL slug
    print("Account " + account_fph)

    payer_account_fph, \
    payer_account_hrns, \
    etype, \
    m = identify_entity(account_fph)

    if not account_fph:
        flash("The FPH in the URL cannot be identified.")
#        return redirect("/home")
        return redirect("/account")
    elif etype != "account":
        flash("The FPH in the URL does not identify an account.")
#        return redirect("/home")

    payer_currency_fph, \
    payer_owner_fph, \
    payer_balance, \
    m = get_account_specific_properties(payer_account_fph)
    if m:
        flash(m)
        #return redirect("/home")
        return redirect("/account")
    if payer_owner_fph != identity_fph:
        flash(
            "Account " + payer_account_hrns + " does not belong to " \
            + identity_hrns
        )
#        return redirect("/home")

    #currency_hrns = fph_to_hrns(payer_currency_fph)
    currency_fph, \
    currency_hrns, \
    currency_prefix, \
    currency_suffix, \
    stewards_list, \
    m = get_currency_specific_properties(payer_currency_fph)

    # If control reaches this point, it has been established that the *account*
    # specified in the URL slug belongs to the current user.
    #
    form = PaymentToAccountForm()
    if form.validate_on_submit():

        payee_identifier = form.to_account_id.data # HRNS or FPH
        #payee_identifier = form.payee_account_identifier.data # HRNS or FPH
#        amount = int(form.amount.data)
        amount_entered = form.amount.data
#        amount = int((form.amount.data)*100)
        annotation = form.annotation.data

        print("payee_identifier     = " + payee_identifier)
        #print("amount_entered       = " + amount_entered)
        print("amount_entered       = " + str(amount_entered))
        amount = int(round(float(amount_entered)*100))
        print("amount               = " + str(amount))
        print("annotation           = " + annotation)

        payee_account_fph, \
        payee_account_hrns, \
        etype, \
        m = identify_entity(payee_identifier)

        if m:
            print("m                = " + m)

        if etype != "account":
            flash(payee_id + " is not an account")
            return redirect("/account/" + payer_account_fph)

        print("payee_account_fph    = " + payee_account_fph)
        print("payee_account_hrns   = " + payee_account_hrns)
        print("etype                = " + etype)

        if payee_account_fph == payer_account_fph:
            flash("An account cannot pay to itself")
            return redirect("/account/" + payer_account_fph)


        payee_currency_fph, \
        payee_owner_fph, \
        payee_balance, \
        m = get_account_specific_properties(payee_account_fph)

        if payee_currency_fph != payer_currency_fph:
            flash(
                "The payer account  " + payer_hrns + "  and the " \
                + "payee account  " + payee_hrns \
                + "  are not in the same currency."
            )
            return redirect("/account/" + payer_account_fph)

        print("payee balance before payment = " + str(payee_balance))
        print("payer balance before payment = " + str(payer_balance))


        # If control reaches this point, the two *accounts* are in the same
        # *currency* so the payment can be made:
        m = payment(payer_account_fph, payee_account_fph, amount, annotation)
        if m:
            flash(m)
            return redirect("/account/" + payer_account_fph)

        ## TESTSTUFF

        payer_currency_fph, \
        payer_owner_fph, \
        payer_balance, \
        m = get_account_specific_properties(payer_account_fph)

        payee_currency_fph, \
        payee_owner_fph, \
        payee_balance, \
        m = get_account_specific_properties(payee_account_fph)

        print("payee balance after payment = " + str(payee_balance))
        print("payer balance after payment = " + str(payer_balance))

        flash(
            "Payment submitted: " \
            + currency_prefix \
            + integer_to_money_format(amount) \
            + currency_suffix
        )
        #return redirect("/home")
        return redirect("/account/" + payer_account_fph)

        #payer_balance = integer_to_money_format(payer_balance)

    return render_template(
                #"home_account_details.html",
                "account.html",
                title="Account",
                form=form,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                payer_account_fph=payer_account_fph,
                payer_account_hrns=payer_account_hrns,
                account_balance=integer_to_money_format(payer_balance),
                #development_mode=development_mode,
                logged_in=logged_in,
                currency_prefix=currency_prefix,    # just added
                currency_suffix=currency_suffix,    # just added
                currency_fph=currency_fph,          # just added
                currency_hrns=currency_hrns,        # just added
                #account_fph=account_fph,            # just added
                #account_hrns=account_hrns,          # just added
                payer_balance=payer_balance     # just added
           )

# account details page --------------------------------------------------------
#@app.route("/account_details/<account_fph>", methods=["GET", "POST"])
#@login_required
#def account_details(account_fph=None):
#    page = "account_details"
#    group = "home"

#    paying = False
#    logged_in = current_user.is_authenticated

    # The *primid* (or its alias *secid*) logged in currently:
#    identity_fph = current_user.get_id()
#    identity_hrns = fph_to_hrns(identity_fph)

    # (This uses the identify_entity( ) function:)
#    identity_type = fph_to_display_type(identity_fph)

    # If an *account* has been specified (by FPH) in the URL slug
#    print("Account " + account_fph)

#    payer_account_fph, \
#    payer_account_hrns, \
#    etype, \
#    m = identify_entity(account_fph)

#    if not account_fph:
#        flash("The FPH in the URL cannot be identified.")
#        return redirect("/account")
#    elif etype != "account":
#        flash("The FPH in the URL does not identify an account.")
#        return redirect("/account")

#    payer_currency_fph, \
#    payer_owner_fph, \
#    payer_balance, \
#    m = get_account_specific_properties(payer_account_fph)
#    if m:
#        flash(m)
#        return redirect("/account")
#    if payer_owner_fph != identity_fph:
#        flash(
#            "Account " + account_hrns + " does not belong to " \
#            + identity_hrns
#        )
#        return redirect("/account")

    #currency_hrns = fph_to_hrns(payer_currency_fph)
#    currency_fph, \
#    currency_hrns, \
#    currency_prefix, \
#    currency_suffix, \
#    stewards_list, \
#    m = get_currency_specific_properties(payer_currency_fph)









#    return render_template(
                #"home_account_details.html",
#                "account_details.html",
#                title="Account details",
#                form=form,
#                page=page,
#                group=group,
#                identity_type=identity_type,
#                identity_fph=identity_fph,
#                identity_hrns=identity_hrns,
#                payer_account_fph=payer_account_fph,
#                payer_account_hrns=payer_account_hrns,
#                account_balance=integer_to_money_format(payer_balance),
                #development_mode=development_mode,
#                logged_in=logged_in,
#                currency_prefix=currency_prefix,    # just added
#                currency_suffix=currency_suffix,    # just added
#                currency_fph=currency_fph,          # just added
#                currency_hrns=currency_hrns,        # just added
#                payer_balance=payer_balance     # just added
#           )

# stewardships page ----------------------------------------------------------
@app.route("/stewardships/<identity_fph>")
@login_required
def stewardships(identity_fph):
    page = "stewardships"
    group = "home"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "stewardships.html",
                title="Stewardships",
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                logged_in=logged_in,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# MANAGEMENT ==================================================================

# management ------------------------------------------------------------------
@app.route("/manage", methods=["GET", "POST"])
@login_required
def manage():
    page = "manage"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "manage.html",
                title="Manage your SLATE settings",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# manage own identities -------------------------------------------------------
@app.route("/identities/manage", methods=["GET", "POST"])
@login_required
def manage_own_identities():
    page = "manage_identities"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False

    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    secids_a = list_secids(primid_fph)
    secids = []
    for s in secids_a:
        if s != "":
            print(s)
            secid = {}
            secid["fph"] = s
            secid["hrns"] = fph_to_hrns(s)
            secids.append(secid)

    return render_template(
                "identities_manage.html",
                title="Manage own identities",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# manage another's identities -------------------------------------------------
@app.route("/identity/manage", methods=["GET", "POST"])
@login_required
def manage_identity():
    page = "manage_identity"
    group = "management"
    #identity_fph = current_user
    #identity_hrns = fph_to_hrns(identity_fph)
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "identity_manage.html",
                title="manage an identity",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# create a new secondary identity ---------------------------------------------
@app.route("/identity/create/secondary", methods=["GET", "POST"])
@login_required
def create_secondary_identity():
    page = "identity_create_secondary"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "identity_create_secondary.html",
                title="Create a new secondary identity",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
            )

# manage own accounts ---------------------------------------------------------
@app.route("/accounts/manage", methods=["GET", "POST"])
@login_required
def manage_accounts():
    page = "manage_accounts"
    group = "management"
    namespace_steward = True
    currency_steward = True

    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    # Since a user may have accounts scattered across an arbitrary number of
    # namespaces, it is necessary to maintain a list of these:
    accounts_a = list_accounts(agent_identifier)
    accounts = []
    for s in accounts_a:
        if s != "":
            print(s)
            a = {}
            a["fph"] = s
            a["hrns"] = fph_to_hrns(s)
            accounts.append(a)
    # (This duplicates code in /home so, like much else, need to be factorized.)

    return render_template(
                "accounts_manage.html",
                title="Manage own accounts",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# manage another's account ----------------------------------------------------
@app.route("/account/manage", methods=["GET", "POST"])
@login_required
def manage_account():
    page = "manage_account"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = True
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "account_manage.html",
                title="Manage own account",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# create a new account --------------------------------------------------------
@app.route("/account/create", methods=["GET", "POST"])
@login_required
def create_account():
    page = "account_create"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "account_create.html",
                title="Create a new account",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# manage own currencies -------------------------------------------------------
@app.route("/currencies/manage", methods=["GET", "POST"])
@login_required
def manage_currencies():
    page = "manage_currencies"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "currencies_manage.html",
                title="Manage currencies",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# manage a currency -----------------------------------------------------------
@app.route("/currency/manage", methods=["GET", "POST"])
@login_required
def manage_currency():
    page = "manage_currency"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "currency_manage.html",
                title="Manage a currency",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# create a currency -----------------------------------------------------------
@app.route("/currency/create", methods=["GET", "POST"])
@login_required
def create_currency():
    page = "create_currency"
    group = "management"
    namespace_steward = False
    currency_steward = False
    paying = True
    logged_in = current_user.is_authenticated

    #user = User(identity_fph) # Retrieve the user object
    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    form = CurrencyCreateForm()
    if form.validate_on_submit():
        currency_fph = currency_create(
                          form.currency_hrns.data,
                          form.currency_type.data,
                          form.prefix_symbol.data,
                          form.suffix_symbol.data,
                          form.acct_same_name.data,
                          form.acct_id_parent.data,
                          form.acct_immdt_crtn.data,
                          identity_fph
                       )
        flash(
            "Currency {} [ {} ] created".format(
                form.currency_hrns.data,
                currency_fph
            )
        )
        return redirect("/home")
    return render_template(
                "create_currency.html",
                title="Create a currency",
                logged_in=logged_in,
                page=page,
                group=group,
                form=form,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# manage own namespaces -------------------------------------------------------
@app.route("/namespaces/manage", methods=["GET", "POST"])
@login_required
def manage_namespaces():
    page = "manage_namespaces"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "manage_namespaces.html",
                title="Manage namespaces",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# manage a namespace ----------------------------------------------------------
@app.route("/namespace/manage", methods=["GET", "POST"])
@login_required
def manage_namespace():
    page = "manage_namespace"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "namespace_manage.html",
                title="Manage a namespace",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# create a namespace ----------------------------------------------------------
@app.route("/namespace/create", methods=["GET", "POST"])
@login_required
def create_namespace():
    page = "create_namespace"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    form = NamespaceCreateForm()
    if form.validate_on_submit():
        flash(
            "Namespace created"
        )
        return redirect("/home")
    return render_template(
                "namespace_create.html",
                title="Create a namespace",
                logged_in=logged_in,
                page=page,
                group=group,
                form=form,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# account balances ------------------------------------------------------------
@app.route("/accounts/view", methods=["GET", "POST"])
@login_required
def balances():
    page = "accounts_view"
    group = "accounts_view"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "balances.html",
                title="account balances",
                logged_in=logged_in,
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# account balances (LTE)  -----------------------------------------------------
@app.route("/accounts/view/lte", methods=["GET", "POST"])
@login_required
def balances_lte():
    page = "accounts_view_lte"
    group = "accounts_view"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated
    user = "Phineas Form-Tester"
    accounts = [
        {
            "account_name": "wrenkled.strin",
            "currency": "cardboard.replica",
            "prefix": "G£",
            "suffix": "",
            "balance": "9876.54"
        },
        {
            "account_name": "green.eggs.suess",
            "currency": "geggs.crossword.clue",
            "prefix": "G£",
            "suffix": "",
            "balance": "347.82"
        }
    ]
    return render_template(
                "balances_lte.html",
                title="account balances (legal tender equivalent)",
                accounts=accounts,
                logged_in=logged_in,
                page=page,
                group=group,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# account balances (time) -----------------------------------------------------
@app.route("/accounts/view/htime", methods=["GET", "POST"])
@login_required
def balances_htime():
    page = "accounts_view_htime"
    group = "accounts_view"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated
    user = "Phineas Form-Tester"
    accounts = [
        {
            "account_name": "human-hours.tomorrow.today.yesterday",
            "currency": "hours.here.now",
            "prefix": "",
            "suffix": "h",
            "balance": "347.82"
        },
        {
            "account_name": "the.time.is.out.of.joint.o.cursed.spite",
            "currency": "that.ever.i.was.born.to.set.it.right",
            "prefix": "",
            "suffix": "h",
            "balance": "666.88"
        },
        {
            "account_name": "repent.harlequin",
            "currency": "said.the.ticktock.man",
            "prefix": "",
            "suffix": "h",
            "balance": "76543.21"
        },
    ]
    return render_template(
                "balances_htime.html",
                title="account balances (legal tender equivalent)",
                user=user,
                accounts=accounts,
                logged_in=logged_in,
                page=page,
                group=group,
                development_mode=development_mode,
                namespace_steward=namespace_steward
           )

# account balances (time) -----------------------------------------------------
@app.route("/accounts/view/energy", methods=["GET", "POST"])
@login_required
def balances_energy():
    page = "accounts_view_energy"
    group = "accounts_view"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated
    user = "Phineas Form-Tester"
    accounts = [
        {
            "account_name": "human-hours.tomorrow.today.yesterday",
            "currency": "hours.here.now",
            "prefix": "",
            "suffix": "kWh",
            "balance": "347.82"
        },
        {
            "account_name": "oer.seas.that.have.no.beaches",
            "currency": "to.end.their.waves.upon",
            "prefix": "",
            "suffix": "GeV",
            "balance": "3.1415926"
        },
        {
            "account_name": "i.travelled.with.twelve.peaches",
            "currency": "a.sofa.and.a.swan",
            "prefix": "",
            "suffix": "GeV",
            "balance": "73.21"
        },
    ]
    return render_template(
                "balances_energy.html",
                title="account balances (energy)",
                user=user,
                accounts=accounts,
                logged_in=logged_in,
                page=page,
                group=group,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )

# account balances (others) ---------------------------------------------------
@app.route("/accounts/view/others", methods=["GET", "POST"])
@login_required
def balances_others():
    page = "accounts_view_others"
    group = "accounts_view"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated
    user = "Phineas Form-Tester"
    accounts = [
        {
            "account_name": "knots.crun.clun",
            "currency": "knotted.string",
            "prefix": "",
            "suffix": "h",
            "balance": "111"
        }    ]
    return render_template(
                "balances_others.html",
                title="account balances (legal tender equivalent)",
                user=user,
                accounts=accounts,
                logged_in=logged_in,
                page=page,
                group=group,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )



# transaction loop ------------------------------------------------------------
@app.route("/admin/tloop")   ### IGNORE THIS: it applies only to NESTS
@login_required
def tloop():
    page = "tloop"
    group = "admin"
    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()

#    if is_administrator(identity_fph):
#        flash("You do not have the necessary privileges to access this page.")
#        return redirect(url_for("home"))
#    else:
#        transaction_processing_is_active = transaction_processing_active()
    tloop_is_active = transaction_processing_active()

    form = TQueueForm()
    if form.validate_on_submit():
        activity = form.activity.data
        if activity == "deactivite_loop":
            disable_transaction_processing()
        elif activity == "activite_loop":
            enable_transaction_processing()
        else:
            print("Something wrong in 'tloop()'")
        return redirect(url_for("home"))


    return render_template(
                "tloop.html",
                title="transaction loop",
                logged_in=logged_in,
                page=page,
                group=group,
                form=form,
                tloop_is_active=tloop_is_active,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )



# help ------------------------------------------------------------------------
@app.route("/help")
def help():
    page = "help"
    group = ""
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated
    return render_template(
                "help.html",
                title="help",
                logged_in=logged_in,
                page=page,
                group=group,
                development_mode=development_mode,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward
           )
