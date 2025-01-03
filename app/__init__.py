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


app.config["MAIL_SERVER"] = "localhost"
#app.config["MAIL_PORT"] = 587
#app.config["MAIL_USE_TLS"] = True
app.config["MAIL_PORT"] = 25
app.config["MAIL_USE_TLS"] = False
app.config["RESET_PASS_TOKEN_MAX_AGE"] = 1000000
#app.config["MAIL_USERNAME"] = 'your.email@example.com'
#app.config["MAIL_PASSWORD"] = 'your-email-password'
mail = Mail(app)

#app.config["EXPORT"] = "/srv/slate/export/"
#app.config["IMPORT"] = "/srv/slate/import/"
app.config["EXPORT"] = "export"
app.config["IMPORT"] = "import"

bootstrap = Bootstrap(app)

# See https://stackoverflow.com/questions/
#     55503515/flask-jinja-template-format-a-string-to-currency
#@app.template_filter()
#def currencyFormat(value):
#    value = float(value)
#    return "${:,.2f}".format(value)


from app import routes, errors

# * see https://pypi.org/project/Flask-Bcrypt/
