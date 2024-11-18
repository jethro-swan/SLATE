from flask import Flask
from config import Config
from flask_login import LoginManager
#from flask_bcrypt import Bcrypt # added 2024-11-10 *
from flask_bootstrap import Bootstrap

app = Flask(__name__)
#bcrypt = Bcrypt(app) # added 2024-11-10 *
app.config.from_object(Config)
login_manager = LoginManager(app)

bootstrap = Bootstrap(app)

from app import routes, errors

# * see https://pypi.org/project/Flask-Bcrypt/
