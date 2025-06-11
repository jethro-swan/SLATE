#!/usr/bin/bash

# NB, if working on a copy rsynced to the target VM (ather than cloned from the
# repository) do not run this script until the venv/ directory has been deleted
# and a fresh virtual environnment has been created using
#    python3 -m venv venv

python3 -m venv venv
HERE=`pwd`
cat $HERE > $HERE/venv/lib/python3.*/site-packages/slate.pth

cd venv

pip install bcrypt
pip install xxhash
pip install email_validator

#pip install Werkzeug
pip install flask
pip install flask_wtf
pip install flask_login
pip install flask_mailman
pip install MarkupSafe
pip install itsdangerous
pip install python-dotenv
pip install flask_bootstrap
pip install gunicorn
#pip install WTForms
#pip install Flask-Bootstrap
#pip install Flask-Login
#pip install Flask-Mailman
#pip install Flask-WTF
#pip install Jinja2

pip install prettytable
pip install prettyprint
pip install wonderwords

pip install Faker

pip install arrow
pip install pypng
pip install pyqrcode
