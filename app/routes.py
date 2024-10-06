import os
import json
from pathlib import Path
import sys

# SLATE components: -----------------------------------------------------------

from app.core.constants import NSS
from app.core.fph_hrns_maps import hrns_to_fph, fph_to_hrns
from app.core.slate_core import get_entity_type, get_account_currency
from app.core.regexp_list import re_fph, re_hrns, re_email
from app.core.auth import pin_random_ord, pin_prompt_message
from app.core.auth import authenticate_pin, authenticate_web_access
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
def fph_to_display_type(identity_fph):
    fpath = fph_to_dpath(identity_fph) + "/.type"
    with open(fpath, "r") as type_f:
        type = type_f.read()
    if type == "primid":
        return "primary identity"
    elif type == "secid":
        return "secondary identity"
    else:
        return ""

# The primary identity need only be displayed if the current active identity is
# a secid:
def fph_to_primid_iff_needed(identity_fph):
    dpath = fph_to_dpath(identity_fph)
    with open(dpath + "/.type", "r") as type_f:
        type = type_f.read()
    if type == "secid":
        with open(fpath + "/.primid", "r") as primid_f:
            primid_fph = primid_f.read()
        primid = {}
        primid["fph"] = primid_fph
        primid["hrns"] = fph_to_hrns(primid_fph)
        return primid
    else:
        return ""



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
    url_parent_namespace_fph = request.args.get("ns_fph")
    url_initial_currency_fph = request.args.get("c_fph")

    initial_namespace_fph = ""
    initial_namespace_hrns = ""
    initial_currency_fph = ""
    initial_currency_hrns = ""

    if url_parent_namespace_fph:
        if not re_fph.match(url_parent_namespace_fph):
            flash("The FPH is invalid.")
            redirect("/register")
        dpath = fph_to_dpath(url_parent_namespace_fph)
        # If dpath is "" then this namespace FPH does not exist:
        if not dpath:
            flash("The namespace FPH in the URL does not exist.")
            redirect("/register")
        else:
            with open(dpath + "/.type", "r") as type_f:
                type = type_f.read()
            if type == "namespace":
                initial_namespace_fph = url_parent_namespace_fph
                initial_namespace_hrns = fph_to_hrns(initial_namespace_fph)
            else:
                flash("The FPH in the URL is not that of a namespace.")
                redirect("/register")

    if url_initial_currency_fph:
        if not re_fph.match(url_initial_currency_fph):
            flash("The FPH is invalid.")
            redirect("/register")
        dpath = fph_to_dpath(url_initial_currency_fph)
        # If dpath is "" then this currency FPH does not exist:
        if not dpath:
            flash("The currency FPH in the URL does not exist.")
            redirect("/register")
        else:
            with open(dpath + "/.type", "r") as type_f:
                type = type_f.read()
            if type == "currency":
                initial_currency_fph = url_initial_currency_fph
                initial_currency_hrns = fph_to_hrns(initial_currency_fph)
            else:
                flash("The FPH in the URL is not that of a currency.")
                redirect("/register")
            # The policy set by the currency's stewards determines which
            # of the fields will be displayed in the registration form:
            #with open(dpath + '/.policy', 'r') as policy_f:
            #    policy = json.load(policy_f)


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

    form = RegistrationForm()
    # The drop-down version commented out below works, but is more trouble than
    # it's worth ...
    #test_root = ROOTS + "/4fdcca5ddb678139"
    #namespaces = build_namepace_list(test_root)
    #choices = []
    #for namespace in namespaces:
    #    choices.append((namespace, hrns_to_fph(namespace)))

    #print("here" + "!"*55)

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
                form.username.data + "." + form.namespace.data,
                form.currency.data,
#                form.country.data,
#                form.county.data,
#                form.town.data,
#                form.village.data,
#                form.bld_number.data,
#                form.bld_name.data,
#                form.flat_number.data,
#                form.room_number.data,
#                form.postal_code.data,
#                form.grid_ref.data,
#                form.olc.data,
#                form.utm_coord.data,
                form.email_1.data,
#                form.save_email_1.data,
                form.email_2.data,
#                form.save_email_2.data,
#                form.phone_num_1.data,
#                form.save_phone_1.data,
#                form.phone_num_2.data,
#                form.save_phone_2.data,
#                form.recovery_a_1.data,
#                form.recovery_q_1.data,
#                form.recovery_a_2.data,
#                form.recovery_q_2.data,
#                form.ssh_pubkey.data,username, namespace
                form.password.data,
                form.password_repeat.data,
                form.pin.data
            )
        )
        # At this point the initial currency may have been specified in either
        # the URL or the form. If the currency FPH was specified in the URL,
        # the currency HRNS field will not have been displayed.
        if form.currency.data:
            currency_hrns = form.currency.data  # from form
            if not re_hrns.match(currency_hrns):
                flash("The currency format is invalid.")
                redirect("/register")
            else:
                dpath = hrns_to_dpath(currency_hrns)
                if not os.path.exists(dpath):
                    flash("The currency specified does not exist.")
                    redirect("/register")
                else:
                    with open(dpath + "/.type", "r") as type_f:
                        type = type_f.read()
                    if not (type == "currency"):
                        flash("The entity specified is not a currency.")
                        redirect("/register")
                # If control reaches this point then the currency specified in
                # the form exists.
                currency_fph = hrns_to_fph(currency_hrns)
        else:
            currency_hrns = initial_currency_hrns # already validated
            currency_fph = initial_currency_fph # already validated

        # Similarly, at this point the parent namespace may have been specified
        # in either the URL or the form. If the parent namespace FPH was
        # specified in the URL, the currency HRNS field will not have been
        # displayed.
        if form.namespace.data:
            parent_namespace_hrns = form.namespace.data
            if not re_hrns.match(parent_namespace_hrns):
                flash("The namespace format is invalid.")
                redirect("/register")
            else:
                dpath = hrns_to_dpath(parent_namespace_hrns)
                if not os.path.exists(dpath):
                    flash("The namespace specified does not exist.")
                    redirect("/register")
                else:
                    with open(dpath + "/.type", "r") as type_f:
                        type = type_f.read()
                    if not (type == "namespace"):
                        flash("The entity specified is not a namespace.")
                        redirect("/register")
                # If control reaches this point then the namespace specified in
                # the form exists.
                parent_namespace_fph = hrns_to_fph(parent_namespace_hrns)
        else:
            parent_namespace_hrns = initial_namespace_hrns # already validated
            parent_namespace_fph = initial_namespace_fph # already validated

        # The parent namespace needs to be completed if any of the ancestor
        # namespaces are missing. Any intermediate namespaces created will be
        # assigned the stewardship of the most recent ancestor namespace.
#        namespace_create(parent_namespace_hrns, "")

        # The username entered may include intermediate namespaces. These need
        # to be created and their initial stewardship assigned to this new
        # identity. However, the stewardship cannot be assigned until this
        # identity has been created (i.e. until we have its FPH) so for the
        # time being
        username_entered = form.username.data
        username_with_ns = username_entered.split(NSS)
        username = username_with_ns[0]
        print("Identity name = " + username_with_ns[0])
        for name in username_with_ns:
            if not name == username_with_ns[0]:
                print("    intermediate namespace = " + name)

        # The full HRNS, including any new intermediate namespaces, is now
        # completed with stewardship assigned to a placeholder pseudo-FPH (all
        # zeros):
        steward_fph_placeholder = "0000000000000000"
        if len(username_with_ns) > 1:
            intermediate_namespaces = ".".join(username_with_ns[1:]) + "."
        else:
            intermediate_namespaces = ""
        print("intermediate_namespaces = " + intermediate_namespaces)
        parent_namespace_path = intermediate_namespaces + parent_namespace_hrns
        print("parent_namespace_path = " + parent_namespace_path)
        primid_hrns = username_entered + "." + parent_namespace_path
#        namespace_create(
#            parent_namespace_path,
#            steward_fph_placeholder
#        )
        # (Although the FPH of the terminal intermediate namespace is returned,
        # it is of no use here.)
        print("New user: " + primid_hrns + " (" + form.email_1.data + ")")
        print("\t\t" + form.password.data + " | " + form.pin.data)

        primid_rv = primid_create(
                        username,
                        parent_namespace_path,
                        currency_fph,
                        form.password.data,
                        form.pin.data,
                        form.email_1.data,
                        form.email_2.data
                    )
        print("primid_rv[0] = " + primid_rv[0])
        print("primid_rv[1] = " + primid_rv[1])
        if primid_rv[1].strip() != "":
            flash(primid_rv[1])     # Error message
            return redirect("/register")   # Try again
        if primid_rv[0] == "":
            log_event(
                "error",
                "no FPH returned"
            )
            flash("internal error - no FPH returned")
            return redirect("/register")   # Try again
        elif not re_fph.match(primid_rv[0]):
            log_event(
                "error",
                "internal error - bad FPH returned"
            )
            flash("internal error - bad FPH returned")
            return redirect("/register")   # Try again
        else:
            user_fph = primid_rv[0]
            flash(primid_hrns + " registered")
            print("user_fph = " + user_fph)
            return redirect("/login")

        # If control has reached this point then the new identity has been
        # created. We now need to assign it stewardship of the newly-created
        # intermediate namespaces.
#        os.chdir(fph_to_dpath(user_fph))    # Enter the new identity's
#        parent_namespace_reached = False    # parent namespace directory.
#        while not parent_namespace_reached:
#            os.chdir("..")
#            with open(".stewards", "r") as stewards_f:
#                stewards = stewards_f.read()
#            if stewards == steward_fph_placeholder:
#                with open(".stewards", "a") as stewards_f:
#                    stewards_f.write(user_fph)
#                    with open(".fph", "r") as fph_f:
#                        fph_here = fph_f.read()
#                    fpath = fph_to_dpath(user_fph) + ".stewards"
#                    with open(fpath, "a") as stewards_f:
#                        stewards_f.write(fph_here)
#            else:
#                parent_namespace_reached = True

        # Whenever a new identity is created, an account is created using the
        # currency's name (not its complete HRNS, just the contents of its .name
        # file) in the identity's namespace.
#        dpath = fph_to_dpath(currency_fph)
#        with open(dpath + "/.name", "r") as name_f:
#            currency_name = name_f.read()
#        account_hrns = currency_name + "." + fph_to_hrns(user_fph)
#        print("account_hrns = " + account_hrns)
#        account_fph = account_create(
#                        account_hrns,
#                        currency_fph,
#                        user_fph,
#                        user_fph
#                      )

#        return redirect("/login")
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
        identity_hrns = form.identity.data
        identity_email = form.email.data

        print("identity_hrns = [" + identity_hrns + "]")

        identity_fph = identity_fph_2 = ""

        if (identity_hrns == "") and (identity_email == ""): # neither provided
            flash("Either an identity or an email address must be provided")
            return redirect(url_for("login"))
        if identity_hrns:
            if not re_hrns.match(identity_hrns):
                flash("The identity HRNS is invalid.")
                return redirect(url_for("login"))
            else:
                identity_fph = hrns_to_fph(identity_hrns)
                print("identity_fph = " + identity_fph + " > " + identity_hrns)
                # Returns "" if the identity is not registered.

                identity_fip = fph_to_fip(identity_fph)

                if not identity_fip: # SOMETHING WRONG/MISSING HERE!!!!
                #if not identity_fph: # SOMETHING WRONG/MISSING HERE!!!!
                    flash("This identity is not registered here.")
                    return redirect(url_for("login"))
                else:
                    dpath = ROOTS + "/" + identity_fip

                print("identity_hrns > identity_fph = " + identity_fph)

        # If control reaches this point, we have a valid identity for the
        # HRNS entered.
        if identity_email:
            if not re_email.match(identity_email):
                flash("The email address is invalid.")
                return redirect(url_for("login"))
            else:
                identity_fph_2 = email_to_fph(identity_email)
                # Returns "" if the email address is not mapped to an identity
                # FPH.
                if not identity_fph_2:
                    flash("This email is not registered here.")
                    return redirect(url_for("login"))
        # If control reaches this point, we have a valid identity for the
        # email address entered.

        if identity_fph and identity_fph_2: # both have been provided
            if identity_fph != identity_fph_2:
                flash("The email address does not belong to this identity.")
                return redirect(url_for("login"))
        #elif identity_fph_2:
        #    identity_fph = identity_fph_2


#        print(">>>>>>> identity_fph = " + identity_fph)
#        dpath = fph_to_dpath(identity_fph)
#        print(">>>>>>> dpath = " + dpath)
        # Exit if this FPH does not exist in the entity map:
#        if not dpath:
#            flash("Invalid identity")
#            return redirect(url_for("login"))

        # Retrieve the user object:
        user = User(identity_fph)

        with open(dpath + "/.type", "r") as type_f:
            type = type_f.read()
        if type == "secid":
            with open(dpath + "/.primid", "r") as primid_f:
                primid = primid_f.read()
            if not primid:
                flash("Apparently not a primid")
                return redirect(url_for("login"))
        elif type != "primid":
            # If the entity type is neither a secondary identity nor a primary
            # identity then we need to exit:
            flash("Invalid username")
            return redirect(url_for("login"))

        if not authenticate_web_access(identity_fph, form.password.data):
            flash("Incorrect password")
            return redirect(url_for("login"))

        if not authenticate_pin(identity_fph, form.pse.data, form.pro.data):
            flash("Incorrect PIN digits")
            return redirect(url_for("login"))

        # Set the .authenticated flag:
        fpath = fph_to_dpath(identity_fph) + "/.authenticated"
        if not os.path.exists(fpath):
            Path(fpath).touch()

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
