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
    #user = { "username": "john" }
    #return "Grrrrr!!! Aaarghhh!!"
    return render_template('index.html', title="Home", user=user)
