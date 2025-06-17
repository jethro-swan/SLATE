# Flask components: -----------------------------------------------------------

from flask import render_template
from app import app

from app.core.slate_core import get_hub_mode
from app.core.slate_core import get_version

@app.errorhandler(401)
def access_unauthorized_error(error):
    return render_template(
        "401.html",
        hub_mode = get_hub_mode(),
        version = get_version()
    ), 401

@app.errorhandler(404)
def not_found_error(error):
    return render_template(
        "404.html",
        hub_mode = get_hub_mode(),
        version = get_version()
    ), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template(
        "500.html",
        hub_mode = get_hub_mode(),
        version = get_version()
    ), 500
