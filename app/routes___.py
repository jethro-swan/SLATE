
# Flask components: -----------------------------------------------------------

from flask import render_template, flash, redirect, url_for
from flask import session, g, request
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_login import login_required



from app import app


#------------------------------------------------------------------------------
# TEMPORARY STUFF

user = { "username": "john" }




#------------------------------------------------------------------------------
# Pages for those not logged in:

@app.route('/')
@app.route('/index')
def index():
    user = { "username": "john" }
    return render_template('index.html', title="Home", user=user)

# login -----------------------------------------------------------------------
#@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    page = "login" # Variable used to identify which menu items to display.
#    mode = "logged_out"
#    logged_in = False
    if current_user.is_authenticated: # user is already logged in
#        mode = "logged_in"
#        logged_in = True
        return redirect(url_for("home"))

    #form = LoginForm(pro=pro, pin_prompt=pin_prompt)
    form = LoginForm()
    if form.validate_on_submit():
        identity_hrns = form.identity.data
        identity_email = form.email.data

        print("identity_hrns = [" + identity_hrns + "]")

        #identity_fph = identity_fph_2 = ""

        if (identity_hrns == "") and (identity_email == ""): # neither provided
            flash("Either an identity or an email address must be provided")
            return redirect(url_for("login"))
#        if identity_hrns:
#            if not re_hrns.match(identity_hrns):
#                flash("The identity HRNS is invalid.")
#                return redirect(url_for("login"))
#            else:
#                identity_fph = hrns_to_fph(identity_hrns)
#                print("identity_fph = " + identity_fph + " > " + identity_hrns)
#                # Returns "" if the identity is not registered.
#
#                identity_fip = fph_to_fip(identity_fph)
#
#                if not identity_fip: # SOMETHING WRONG/MISSING HERE!!!!
#                #if not identity_fph: # SOMETHING WRONG/MISSING HERE!!!!
#                    flash("This identity is not registered here.")
#                    return redirect(url_for("login"))
#                else:
#                    dpath = ROOTS + "/" + identity_fip
#
#                print("identity_hrns > identity_fph = " + identity_fph)

        # If control reaches this point, we have a valid identity for the
        # HRNS entered.
        if identity_email:
            if not re_email.match(identity_email):
                flash("The email address is invalid.")
                return redirect(url_for("login"))
#            else:
#                identity_fph_2 = email_to_fph(identity_email)
#                # Returns "" if the email address is not mapped to an identity
#                # FPH.
#                if not identity_fph_2:
#                    flash("This email is not registered here.")
#                    return redirect(url_for("login"))
        # If control reaches this point, we have a valid identity for the
        # email address entered.

#        if identity_fph and identity_fph_2: # both have been provided
#            if identity_fph != identity_fph_2:
#                flash("The email address does not belong to this identity.")
#                return redirect(url_for("login"))
#        #elif identity_fph_2:
#        #    identity_fph = identity_fph_2


#        print(">>>>>>> identity_fph = " + identity_fph)
#        dpath = fph_to_dpath(identity_fph)
#        print(">>>>>>> dpath = " + dpath)
        # Exit if this FPH does not exist in the entity map:
#        if not dpath:
#            flash("Invalid identity")
#            return redirect(url_for("login"))

        # Retrieve the user object:
#        user = User(identity_fph)
        user = User(agent_number)


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
                #development_mode=development_mode
           )










@app.route('/register')
def register():
    return "This will be the registration screen"

@app.route('/login/recover')
def recover():
    return "This will be the login recovery screen"

#-----------------------------------------------------------------------------
# Pages accessible to anyone logged in:

# General agents (users)

@app.route('/home')
#@login_required
def home():
    return "This will be the home screen"

@app.route('/agent/self/update')
#@login_required
def agent_self_update():
    return "This will be the screen for the agent to update its own details"

@app.route('/logout')
def logout():
    return "This will be the logout screen"

@app.route('/pay')
def pay():
    return "This will be the payment screen"

#-----------------------------------------------------------------------------
# Pages accessible only to community stewards:

@app.route('/agent/suspend')
#@login_required
def agent_suspend():
    return "This will be the screen for a steward to suspend an agent"

@app.route('/agent/enable')
#@login_required
def agent_enable():
    return "This will be the screen for a steward to enable an agent"

@app.route('/agent/update')
#@login_required
def agent_update():
    return "This will be the screen for a steward to update an agent's details"

@app.route('/agent/registration/confirm')
#@login_required
def confirm_pending_registration():
    return "This will be the screen for a community steward to confirm a registration"

@app.route('/agent/registration/reject')
#@login_required
def reject_pending_registration():
    return "This will be the screen for a community steward to reject a registration"

#-----------------------------------------------------------------------------
# Pages accessible only to currency stewards:

@app.route('/agent/suspend')
#@login_required
def journal_export():
    return "This will be the screen for a currency steward to export a journal"

@app.route('/payment/list')
#@login_required
def list_payments():
    return "This will be the screen for a currency steward to payments"

@app.route('/payment/reverse')
#@login_required
def reverse_payment():
    return "This will be the screen for a currency steward to reverse a payment"




#-----------------------------------------------------------------------------
# Pages accessible only to global administrators:

@app.route('/community/add')
#@login_required
def add_community():
    return "This will be the community creation screen"

@app.route('/community/steward/list')
#@login_required
def list_community_stewards():
    return "This will be the screen to list communities"

@app.route('/community/steward/add')
#@login_required
def add_community_steward():
    return "This will be the screen to add a community steward"

@app.route('/community/steward/remove')
#@login_required
def remove_community_steward():
    return "This will be the screen to remove a community steward"
