import sqlite3
import random
import os
import pickle
from pathlib import Path

from .constants import ENTITIES_DB
from .regexp_list import *
from .slate_core import get_entity_type, get_primid
#from .slate_login import get_auth_data

debugging = True
#max_hrns_depth = 0

#==============================================================================


#==============================================================================
# Authentication and login managemenet:

def register_authenticated_login(agent_fph): # (agent is *primid* or *secid*)
    if not re_fph.match(agent_fph):
        return False, "", agent_fph + " is not an FPH"
    entity_type , m = get_entity_type(agent_fph)
    if entity_type == "secid":
        primid_fph = get_primid(agent_fph)
        login_id_fph = agent_fph
    elif entity_type == "primid":
        primid_fph = agent_fph
        login_id_fph = agent_fph
    else:
        return False, "", agent_fph + " is FPH of neither primid nor secid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO logins (primid_fph, login_id_fph, login_authenticated)
            VALUES (?, ?, ?)
            """,
            (primid_fph, login_id_fph, True)
        )
        conn.commit()
        cursor.close()
    return primid_fph, login_id_fph, "" # The login_id_fph may be either that
                                        # of the primid or that of a secid
                                        # acting as an alias of it.


#------------------------------------------------------------------------------
def deregister_authenticated_login(agent_fph):
    if not re_fph.match(agent_fph):
        return False, "", agent_fph + " is not an FPH"
    entity_type , m = get_entity_type(agent_fph)
    if entity_type == "secid":
        primid_fph = get_primid(agent_fph)
        login_id_fph = agent_fph
    elif entity_type == "primid":
        primid_fph = agent_fph
        login_id_fph = agent_fph
    else:
        return False, "", "", agent_fph + " is FPH of neither primid nor secid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM login WHERE agent_fph = ?", (agent_fph,))
        conn.commit()
        cursor.close()
    #return primid_fph, login_id_fph
    return True, primid_fph, login_id_fph, ""


#------------------------------------------------------------------------------
def check_authenticated_login(agent_fph):
    if not re_fph.match(agent_fph):
        return False, "", "", agent_fph + " is not an FPH"
    entity_type , m = get_entity_type(agent_fph)
    if entity_type == "secid":
        primid_fph = get_primid(agent_fph)
        login_id_fph = agent_fph
    elif entity_type == "primid":
        primid_fph = agent_fph
        login_id_fph = agent_fph
    else:
        #return False
        return False, "", "", agent_fph + " is FPH of neither primid nor secid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT login_authenticated FROM login WHERE agent_fph = ?
            """,
            (primid_fph,)
        )
        result = cursor.fetchone()
        login_authenticated = result[0]
        #login_id_fph = result[1]
    return login_authenticated, primid_fph, login_id_fph, ""



#------------------------------------------------------------------------------

def get_auth_data(primid_fph):

#    auth_dict = {}
#    auth_dict["password_hash"] = ""
#    auth_dict["pin"] = ""
#    auth_dict["access_token_hash"] = ""

    if not re_fph.match(primid_fph):
#        return auth_dict, primid_fph + " is not an FPH"
        return  "", "", "", primid_fph + " is not an FPH"
        
    entity_type, m = get_entity_type(primid_fph)
    if m:
#        return auth_dict, m
        return "", "", "", m
    if entity_type != "primid":
#        return auth_dict, primid_fph + " is not a primid"
        return "", "", "", primid_fph + " is not a primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT password_hash, pin, access_token_hash
            FROM primids WHERE entity_fph = ?
            """,
            (primid_fph,)
        )
        result = cursor.fetchone()
#    auth_dict = {}
#    auth_dict["password_hash"] = result[0]
#    auth_dict["pin"] = result[1]
#    auth_dict["access_token_hash"] = result[2]
#    return auth_dict, ""
    return result[0], result[1], result[2], ""

#==============================================================================
