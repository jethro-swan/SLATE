import os
import json
from pathlib import Path
import sys

from flask-bcrypt import Brypt  # 2024-11-10: Try this out to resolve problem
                                # with check_auth_hash( )
                                # ("ValueError: Invalid salt")

# SLATE components: -----------------------------------------------------------

from app.core.constants import NSS
from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.slate_core import get_entity_type, get_account_currency
from app.core.slate_core import identify_entity, get_primid
from app.core.slate_core import new_primid
from app.core.slate_core import retrieve_primid_access_details
from app.core.regexp_list import re_fph, re_hrns, re_email
from app.core.slate_login import get_auth_data
from app.core.auth import pin_random_ord, pin_prompt_message
from app.core.auth import check_auth_hash, authenticate_pin
from app.core.logging import log_event

from app.core.display import yesno



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
from app.forms import PaymentToAccountHRNSForm, PaymentToIdentityHRNSForm
from app.forms import PaymentToAccountFPHForm, PaymentToIdentityFPHForm
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
    etype, m = get_entity_type(identity_fph)
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
    # initial currency and namespace. For example, for some currencies (many
    # perhaps) it may be considered very useful to have some information about
    # the geographical location of the user's base (home or business address),
    # particularly where this is going to be used to create a map overlay.

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
        # At this point the initial currency may have been specified in either
        # the URL or the form. If the currency FPH was specified in the URL,
        # the currency HRNS field will not have been displayed.

        currency_identifier = form.currency.data  # from form
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

        # Similarly, at this point the parent namespace may have been specified
        # in either the URL or the form. If the parent namespace FPH was
        # specified in the URL, the currency HRNS field will not have been
        # displayed.

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
        # If control reaches this point then either the *namespace* specified
        # in the form or the  *namespace* specified in the URL exists.

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
            identity_fph = get_primid(identity_fph)
            if m:
                flash(m)
                return redirect(url_for("login"))
            else:
                identity_hrns = fph_to_hrns(identity_fph)
        if not identity_fph:
            flash("This identity is not registered here.")
            #return redirect(url_for("login"))

        print("identity = " + identity_fph + " = [" + identity_hrns + "]")

        # If control reaches this point and the FPH exists, we have a valid
        # *primid* for the HRNS or FPH entered.
        if identity_fph:
            flash(
                identity_hrns + " = [" + identity_fph + "] has " \
                + "been identified from the agent identifier."
            )
            primid_identified_has_been_from_identity = True

        if identity_email:
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

            # If control reaches this point, we have a valid identity for the
            # email address entered.

        # Whether from the agent field (*primid*|*secid*) or from an email
        # address, we have now identified the *primid*.
        print("identity = " + identity_fph + " = [" + identity_hrns + "]")

#        auth_dict, m = get_auth_data(identity_fph)
#        if m:
#            flash(m)
#            return redirect(url_for("login"))
#        password_hash = auth_dict["password_hash"]
#        pin = auth_dict["pin"]
#        access_token_hash = auth_dict["access_token_hash"]

        password_hash, \
        pin, \
        access_token_hash, \
        m = get_auth_data(identity_fph)
        if m:
            flash(m)
            return redirect(url_for("login"))

        print("password hash = " + password_hash)
        print("PIN = " + pin)
        print("access_token_hash = " + access_token_hash)



#        password_hash, \
#        pin, \
#        access_token_hash, \
#        m = retrieve_primid_access_details(identity_fph)

        # Retrieve the user object:
        user = User(identity_fph)


        password = form.password.data
        print("form.password.data = " + form.password.data)
        password2 = form.password.data.strip()
        print("password strip()ped = " + form.password.data)
        if password != password2:
            print("password corrupted")


# Some test stuff ...

        import bcrypt
        salt = password_hash[:29]
        print("salt (d)  = ", end="")
        print(salt)
        print("salt (e)  = ", end="")
        print(salt.encode("utf-8"))
        pwhe = password_hash.encode("utf-8")
        pw2e = password2.encode("utf-8")
        print("password  = " + password)
        print("password2 = " + password2)
        print("pwhe      = " + str(pwhe))
        print("pw2e      = " + str(pw2e))
        r = bcrypt.checkpw(pwhe, pw2e)
        print("checkpw ... " + yesno(r))







        #if not authenticate_web_access(identity_fph, form.password.data):
        if not check_auth_hash(password_hash, password):
        #if not check_auth_hash(password_hash, form.password.data):
            flash("Incorrect password")
            return redirect(url_for("login"))

        if not authenticate_pin(identity_fph, form.pse.data, form.pro.data):
            flash("Incorrect PIN digits")
            return redirect(url_for("login"))

        # Register the authenticated login:
        register_authenticated_login(identiy_fph)

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
    print("current_user = " + user)
    current_user.mark_unauthenticated()

    logout_user()
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
        identity_hrns = form.identity.data
        identity_fph = form.fph.data
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
        identity_fip = fph_to_fip(identity_fph)
        # Returns "" if the identity is not registered.
        if not identity_fip: # no email > FPH mapping found
            flash("This identity is not registered here.")
            return redirect(url_for("login"))
        dpath = ROOTS + identity_fip
        with open(dpath + "/.type", "r") as type_f:
            type = type_f.read()
        if not ((type == "primd") or (type == "secid")):
            flash("This is not registered identity.")
            return redirect(url_for("login"))
        elif (type == "secid"):
            with open(dpath + "/.primd", "r") as primid_f:
                primid_fph = primid_f.read()
        else:
            primid_fph = identity_fph
        # If control reaches this point, we have a valid identity for the HRNS
        # entered.
        if not identity_email:
            flash("Login recovery is not possible without an email address.")
            return redirect(url_for("login"))
        elif not re_email.match(identity_email):
            flash("The email address is invalid.")
            return redirect(url_for("login"))
        else:
            identity_fph_2 = email_to_fph(identity_email)
            # Returns "" if the email address is not mapped to an identity FPH.
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
    #identity_type = "primary" # User always logs in using primary identity
    #identity_fph = "625f14ca724ce4fa" # jim.moriarty.gamma.delta.test
    #identity_hrns = "jim.moriarty.gamma.delta.test"
    #identity_fph = current_user
    #identity_hrns = fph_to_hrns(identity_fph)
    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)
    # The primary_identity string is "" if the current active identity is
    # a primid:
    primid_iff_needed = fph_to_primid_iff_needed(identity_fph)

    # Since a user may have accounts scattered across an arbitrary number of
    # namespaces, it is necessary to maintain a list of these:
    dpath = fph_to_dpath(identity_fph)
    with open(dpath + "/.accounts") as accounts_f:
        account_list = accounts_f.read()
    accounts_a = account_list.split("\n")
    accounts = []
    for s in accounts_a:
        if s != "":
            print(s)
            account = {}
            account["fph"] = s
            account["hrns"] = fph_to_hrns(s)
            accounts.append(account)

    dpath = fph_to_dpath(identity_fph)
    with open(dpath + "/.secid_list") as secids_f:
        secid_list = secids_f.read()
    secids_a = secid_list.split("\n")
    secids = []
    for s in secids_a:
        if s != "":
            print(s)
            secid = {}
            secid["fph"] = s
            secid["hrns"] = fph_to_hrns(s)
            secids.append(secid)

    return render_template(
                "home.html",
                title="Home",
                page=page,
                group=group,
                development_mode=development_mode,
                logged_in=logged_in,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                primid_iff_needed=primid_iff_needed,
                accounts=accounts,
                secids=secids
           )

# account details page --------------------------------------------------------
@app.route("/account/")
@app.route("/account/<account_fph>")
@login_required
def account_details(account_fph=None):
    page = "account_details"
    group = "home"
    #mode = ""
    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    if account_fph is not None:

        #account_fph = request.args.get("a_fph")
        if not re_fph.match(account_fph):
            flash(
                account_fph + " is not a valid FPH"
            )
            return redirect("/home")
        account_hrns = fph_to_hrns(account_fph)
        if not account_hrns:
            flash(
                "There is no account with FPH " + account_fph
            )
            return redirect("/home")
        dpath = fph_to_dpath(account_fph)
        with open(dpath + "/.type", "r") as type_f:
            type = type_f.read()
        if not type == "account":
            flash(
                account_fph + " is not an account"
            )
            return redirect("/home")

    else:

        flash(
            "No account FPH specified."
        )
        return redirect("/home")




    return render_template(
                #"home_account_details.html",
                "account_details.html",
                title="Accounts",
                page=page,
                group=group,
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,
                development_mode=development_mode,
                logged_in=logged_in,
                namespace_steward=namespace_steward,
                currency_steward=currency_steward,
                account_fph=account_fph,
                account_hrns=account_hrns
           )

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

# PAYMENTS ====================================================================

# make a payment --------------------------------------------------------------
@app.route("/pay", methods=["GET", "POST"])
@login_required
def pay():
    page = "pay"
    group = "payment"
    namespace_steward = True
    currency_steward = True
    paying = True
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "pay.html",
                title="Make a payment",
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

# payment to account ----------------------------------------------------------
@app.route("/pay/account", methods=["GET", "POST"])
@login_required
def pay_account():
    page = "pay_account"
    group = "payment"
    namespace_steward = True
    currency_steward = True
    paying = True
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    form = PaymentToAccountForm()
    if form.validate_on_submit():
        flash(
            "Payment submitted to account {}".format(
                form.to_account_hrns.data,
                form.to_account_fph.data,
                form.amount.data,
                form.annotation.data
            )
        )
        return redirect("/home")
    return render_template(
                "pay_account.html",
                title="Payment to known account",
                form=form,
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

# payment to account HRNS ----------------------------------------------------
@app.route("/pay/account/hrns", methods=["GET", "POST"])
@login_required
def pay_account_hrns():
    page = "pay_account_hrns"
    group = "payment"
    namespace_steward = True
    currency_steward = True
    paying = True
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    form = PaymentToAccountHRNSForm()
    if form.validate_on_submit():
        flash(
            "Payment submitted to account {}".format(
                form.to_account_hrns.data,
                form.amount.data,
                form.annotation.data
            )
        )
        return redirect("/home")
    return render_template(
                "pay_account_hrns.html",
                title="Payment to known account (HRNS)",
                form=form,
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

# payment to account FPH ------------------------------------------------------
@app.route("/pay/account/fph", methods=["GET", "POST"])
@login_required
def pay_account_fph():
    page = "pay_account_fph"
    group = "payment"
    payer_fph = current_user.get_id()
    namespace_steward = True
    currency_steward = True
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    form = PaymentToAccountFPHForm()
    if form.validate_on_submit():
        payee_fph = form.to_account_fph.data
        amount = form.amount.data
        annotation = form.annotation.data
        if entity_type(payee_fph) != "account":
            flash(payee_fph + " is not an account")
            return redirect("/pay/account/fph")
        currency_fph = account_currency(payee_fph)
        accounts_list = currency_accounts(payer_fph)
        usable_account_found = ""
        for account_fph in accounts_list:
            if account_currency(account_fph) == currency_fph:
                usable_account_found = account_fph
        if not usable_account_found:
            flash("None of your accounts uses " + payee_fph + "'s currency." )
            return redirect("/pay/account/fph")
        schedule_payment(payer_fph, payee_fph, amount, annotation)
        flash(
            "Payment submitted to account {}".format(
                form.to_account_fph.data,
                form.amount.data,
                form.annotation.data
            )
        )
        return redirect("/home")
    return render_template(
                "pay_account_fph.html",
                title="Payment to known account (FPH)",
                form=form,
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

# payment to identity ---------------------------------------------------------
@app.route("/pay/identity", methods=["GET", "POST"])
@login_required
def pay_identity():
    page = "pay_identity"
    group = "payment"
    namespace_steward = True
    currency_steward = True
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    form = PaymentToIdentityForm()
    if form.validate_on_submit():
        flash(
            "Payment submitted to identity {}".format(
                form.to_identity_hrns.data,
                form.to_identity_fph.data,
                form.currency_hrns.data,
                form.currency_fph.data,
                form.amount.data
            )
        )
        return redirect("/home")
    return render_template(
                "pay_identity.html",
                title="Payment to known identity",
                form=form,
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

# payment to identity HRNS ---------------------------------------------------
@app.route("/pay/identity/hrns", methods=["GET", "POST"])
@login_required
def pay_identity_hrns():
    page = "pay_identity_hrns"
    group = "payment"
    namespace_steward = True
    currency_steward = True
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    form = PaymentToIdentityHRNSForm()
    if form.validate_on_submit():
        flash(
            "Payment submitted to identity {}".format(
                form.to_identity_hrns.data,
                form.amount.data
            )
        )
        return redirect("/home")
    return render_template(
                "pay_identity_hrns.html",
                title="Payment to known identity (HRNS)",
                form=form,
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

# payment to identity FPH -----------------------------------------------------
@app.route("/pay/identity/fph", methods=["GET", "POST"])
@login_required
def pay_identity_fph():
    page = "pay_identity_fph"
    group = "payment"
    namespace_steward = True
    currency_steward = True
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    form = PaymentToIdentityFPHForm()
    if form.validate_on_submit():
        flash(
            "Payment submitted to identity {}".format(
                form.to_identity_fph.data,
                form.amount.data
            )
        )
        return redirect("/home")
    return render_template(
                "pay_identity_fph.html",
                title="Payment to known identity (FPH)",
                form=form,
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

# payment unsuccessful: account HRNS invalid ----------------------------------
#@app.route("/pay/unsuccessful/hrns_invalid", methods=["GET", "POST"])
#def payment_hrns_failure():
#    page = "payment_hrns_invalid"
#    mode = "payment"
#    #identity_fph = current_user
#    #identity_hrns = fph_to_hrns(identity_fph)
#    namespace_steward = False
#    currency_steward = False
#    paying = True
#    logged_in = current_user.is_authenticated
#    return render_template(
#                "payment_hrns_invalid.html",
#                title="Payment account name (HRNS) is invalid",
#                logged_in=logged_in,
#                page=page,
#                group=group,
#                development_mode=development_mode,
#                #identity_type=identity_type,
#                #identity_fph=identity_fph,
#                #identity_hrns=identity_hrns,
#                namespace_steward=namespace_steward,
#                currency_steward=currency_steward,
#                paying=paying
#           )

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
                title="Manage your NESTS",
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
    page = "identities_manage"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False

    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    dpath = fph_to_dpath(identity_fph)
    with open(dpath + "/.secid_list") as secids_f:
        secid_list = secids_f.read()
    secids_a = secid_list.split("\n")
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
    page = "identity_manage"
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
    page = "accounts_manage"
    group = "management"
    namespace_steward = True
    currency_steward = True

    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    # Since a user may have accounts scattered across an arbitrary number of
    # namespaces, it is necessary to maintain a list of these:
    dpath = fph_to_dpath(identity_fph)
    with open(dpath + "/.accounts") as accounts_f:
        account_list = accounts_f.read()
    accounts_a = account_list.split("\n")
    accounts = []
    for s in accounts_a:
        if s != "":
            print(s)
            account = {}
            account["fph"] = s
            account["hrns"] = fph_to_hrns(s)
            accounts.append(account)
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
    page = "account_manage"
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
    page = "currencies_manage"
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
    page = "currency_manage"
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
    page = "currency_create"
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
                "currency_create.html",
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
    page = "namespaces_manage"
    group = "management"
    namespace_steward = True
    currency_steward = True
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id()
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    return render_template(
                "namespaces_manage.html",
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
    page = "namespace_manage"
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
    page = "namespace_create"
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
@app.route("/admin/tloop")
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
