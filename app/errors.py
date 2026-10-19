# NESTS/SLATE - a networked tool to support user-created and -stewarded
# currencies and measures (open money and open measure)
# Copyright (C) 2026. 2025, 2024, 2023, 2022 John Waters
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

# Flask components: -----------------------------------------------------------

from flask import flash, redirect, url_for
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
    return redirect(url_for("login"))
#    return render_template(
#        "404.html",
#        hub_mode = get_hub_mode(),
#        version = get_version()
#    ), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template(
        "500.html",
        hub_mode = get_hub_mode(),
        version = get_version()
    ), 500
