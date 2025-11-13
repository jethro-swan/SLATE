import os
from pathlib import Path
from datetime import datetime
import sys
from itsdangerous import URLSafeTimedSerializer

# SLATE components: -----------------------------------------------------------

from app.core.common import unixtime_str, timestamp
#from app.core.common import enabled, pending
from app.core.fph_hrns_maps import hrns_to_fph
#from app.core.auth import set_web_password_hash, authenticate_web_access
#from app.core.auth import authenticate_web_access

from app.core.slate_login import register_authenticated_login
from app.core.slate_login import deregister_authenticated_login
from app.core.slate_login import check_authenticated_login
from app.core.slate_login import get_auth_data
from app.core.auth import check_auth_hash

from app import app

# Flask components: -----------------------------------------------------------

from flask import Flask, Response
#from flask.ext.login import LoginManager, UserMixin, login_required
from flask_login import LoginManager, UserMixin

# See
# https://flask-login.readthedocs.io/en/latest/_modules/flask_login/mixins.html

from app import login_manager


class User(UserMixin):

    def __init__(self, agent_fph):
        self.id = agent_fph

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

#    def set_working_identity(working_identity_fph):
#        self.working_identity_fph = working_identity_fph

#    def get_working_identity(self):
#        return self.working_identity_fph

    def is_authenticated(self):
        #print("is_authenticated: self.id = " + self.id)
        #fpath = fph_to_dpath(self.id) + "/.authenticated"
        #print("is_authenticated: fpath = " + fpath)
        #if os.path.exists(fpath):
        #    return True
        #else:
        #    return False
        return check_authenticated_login(self)

    def mark_authenticated(self):
        #print("mark_authenticated: self.id = " + self.id)
        #fpath = fph_to_dpath(self.id) + "/.authenticated"
        #print("mark_authenticated: fpath = " + fpath)
        #if not os.path.exists(fpath):
        #    Path(fpath).touch()
        agent_fph_fph, \
        login_id_fph, \
        m = register_authenticated_login(self.id)
        return agent_fph, login_id_fph

    def mark_unauthenticated(self):
        #print("mark_unauthenticated: self.id = " + self.id)
        #fpath = fph_to_dpath(self.id) + "/.authenticated"
        #print("mark_unauthenticated: fpath = " + fpath)
        #if os.path.exists(fpath):
        #    os.remove(fpath)
        deregistered, \
        m = deregister_authenticated_login(self.id)
        return deregistered, m
        #primid_fph, login_id_fph, m = deregister_authenticated_login(self)
        #return primid_fph, login_id_fph

#    @staticmethod
#    def validate_login_reset_token(token: str, user_id: str):
#
#        password_hash, \
#        stored_pin, \
#        access_token_hash, \
#        m = get_auth_data(user_id)
#
#        print("SECRET_KEY = " + app.config["SECRET_KEY"])
#
#        serializer = URLSafeTimedSerializer(app.config["SECRET_KEY"])
#        token_user_email = serializer.loads(
#                               token,
#                               max_age=app.config["RESET_PASS_TOKEN_MAX_AGE"],
#                               salt=password_hash
#                           )
#
#        if check_auth_hash(token_user_email, password_hash):
#            return agent_primid_fph
#        else:
#            return None




@login_manager.user_loader
def load_user(user_id):
    return User(user_id)
