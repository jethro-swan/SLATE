import os
from pathlib import Path
from datetime import datetime
import sys

# SLATE components: -----------------------------------------------------------

from app.core.common import unixtime_str, timestamp
#from app.core.common import enabled, pending
from app.core.fph_hrns_maps import hrns_to_fph
#from app.core.auth import set_web_password_hash, authenticate_web_access
from app.core.auth import authenticate_web_access

# Flask components: -----------------------------------------------------------

from flask import Flask, Response
#from flask.ext.login import LoginManager, UserMixin, login_required
from flask_login import LoginManager, UserMixin

# See
# https://flask-login.readthedocs.io/en/latest/_modules/flask_login/mixins.html

from app import login_manager


class User(UserMixin):

    def __init__(self, fph):
        self.id = fph

    def is_active(self):
        #if enabled(self.fph) and not pending(self.fph):
        if enabled(self.id) and not pending(self.id):
            return True
        else:
            return False

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def is_authenticated(self):
        print("is_authenticated: self.id = " + self.id)
        fpath = fph_to_dpath(self.id) + "/.authenticated"
        print("is_authenticated: fpath = " + fpath)
        if os.path.exists(fpath):
            return True
        else:
            return False

    def mark_authenticated(self):
        print("mark_authenticated: self.id = " + self.id)
        fpath = fph_to_dpath(self.id) + "/.authenticated"
        print("mark_authenticated: fpath = " + fpath)
        if not os.path.exists(fpath):
            Path(fpath).touch()

    def mark_unauthenticated(self):
        print("mark_unauthenticated: self.id = " + self.id)
        fpath = fph_to_dpath(self.id) + "/.authenticated"
        print("mark_unauthenticated: fpath = " + fpath)
        if os.path.exists(fpath):
            os.remove(fpath)


#@login.user_loader
@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
