from flask import Flask
from config import Config
from flask_login import LoginManager
#from flask_bcrypt import Bcrypt # added 2024-11-10 *
from flask_bootstrap import Bootstrap

from flask_mailman import Mail

app = Flask(__name__)
#bcrypt = Bcrypt(app) # added 2024-11-10 *
app.config.from_object(Config)
login_manager = LoginManager(app)

mail = Mail(app)




bootstrap = Bootstrap(app)

# See https://stackoverflow.com/questions/
#     55503515/flask-jinja-template-format-a-string-to-currency
#@app.template_filter()
#def currencyFormat(value):
#    value = float(value)
#    return "${:,.2f}".format(value)


from app import routes, errors

# * see https://pypi.org/project/Flask-Bcrypt/
