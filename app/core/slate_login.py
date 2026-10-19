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

import sqlite3
import random
import os
import pickle
from pathlib import Path

from app.core.constants import ENTITIES_DB
from app.core.regexp_list import *
from app.core.slate_core import get_entity_types

from app.core.slate_core import fph_to_hrns
from app.core.slate_core import entity_type_is_registered

debugging = True

#==============================================================================
# Authentication and login managemenet:

def register_authenticated_login(agent_fph): # (agent is *primid*)
    if not re_fph.match(agent_fph):
        return False, "", agent_fph + " is not an FPH"
    elif entity_type_is_registered(agent_fph, "primid"):
        primid_fph = agent_fph
        login_id_fph = agent_fph
    else:
        return False, "", agent_fph + " is FPH of not a *primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO login " \
            + "(entity_fph, login_id_fph, login_authenticated) " \
            + "VALUES (?, ?, ?)",
            (primid_fph, login_id_fph, True)
        )
        conn.commit()
        cursor.close()
    return primid_fph, login_id_fph, "" # The login_id_fph must be a *primid*

#------------------------------------------------------------------------------

def deregister_authenticated_login(agent_fph):
    if not re_fph.match(agent_fph):
        return False, agent_fph + " is not an FPH"
    elif entity_type_is_registered(agent_fph, "primid"):
        primid_fph = agent_fph
        login_id_fph = agent_fph
    else:
        return False, agent_fph + " is not FPH of a primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM login WHERE entity_fph = ?",
            (agent_fph,)
        )
        conn.commit()
        cursor.close()
    return True, ""

#------------------------------------------------------------------------------

def check_authenticated_login(agent_fph):
    if not re_fph.match(agent_fph):
        return False, "", "", agent_fph + " is not an FPH"
    elif entity_type_is_registered(agent_fph, "primid"):
        primid_fph = agent_fph
        login_id_fph = agent_fph
    else:
        return False, "", "", agent_fph + " is FPH not of a primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT login_authenticated FROM login WHERE agent_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        login_authenticated = result[0]
    return login_authenticated, primid_fph, login_id_fph, ""

#------------------------------------------------------------------------------

def get_auth_data(primid_fph):
    if not re_fph.match(primid_fph):
        return  "", "", "", primid_fph + " is not an FPH"
    if not entity_type_is_registered(primid_fph, "primid"):
        return "", "", "", primid_fph + " is not a primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT password_hash, pin, access_token_hash " \
            + "FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
    if result is None:
        return "", "", "", "Authentication data not found"
    return result[0], result[1], result[2], ""

#==============================================================================
