import sqlite3
import pickle

from app.core.slate_core import identify_entity
#from app.core.slate_core import list_stewards
#from app.core.slate_core import list_namespace_stewardships
#from app.core.slate_core import list_currency_stewardships
from app.core.slate_core import set_currency_parameter

from app.core.slate_core import get_namespace_properties
from app.core.slate_core import get_currency_properties

from app.core.slate_core import log_self_repair

from app.core.constants import ENTITIES_DB



#==============================================================================
# List stewards of a *namespace* or *currency*:

def list_stewards(entity_id, etype):
    entity_fph, entity_hrns, etypes, m = identify_entity(entity_id)
    if not entity_fph:
        return [], entity_id + " is not a registered identifier"
    if not (etype in etypes):
        return [], entity_hrns + " has no registered " + etype
    if etype == "namespace":
        tbl = "namespaces"
    elif etype == "currency":
        tbl = "currencies"
    else:
        return [], "Invalid entity type"
#    select_str = "SELECT stewards_fph_list FROM " + tbl \
#               + " WHERE entity_fph = ?"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stewards_fph_list FROM " + tbl + " WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        cursor.close()
        if result is not None:
            stewards_fph_list = pickle.loads(result[0])
            stewards_fph_list = list(set(stewards_fph_list)) # See note 2
        else:
            stewards_fph_list = []
    return stewards_fph_list, ""

#------------------------------------------------------------------------------
# List *namespace* stewardships of a *primid*:

def list_namespace_stewardships(primid_id):
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if m:
        return [], primid_id + " is not a registered identifier"
    if not ("primid" in etypes):
         return [], primid_id + " does not identify a primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT nstewardships_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            nstewardships_fph_list = []
        else:
            nstewardships_fph_list = list(set(pickle.loads(result[0])))
        if not (primid_fph in nstewardships_fph_list):
            # At the very least, the *primid* is a steward of the
            # *namespace* with which it shares an identifier:
            nstewardships_fph_list.append(primid_fph)
            nstewardships_fph_blob = pickle.dumps(nstewardships_fph_list)
            cursor.execute(
                "UPDATE primids SET nstewardships_fph_list = ? " \
                + "WHERE entity_fph = ?",
                (nstewardships_fph_blob, primid_fph)
            )
            conn.commit()
        cursor.close()
    return nstewardships_fph_list, ""

#------------------------------------------------------------------------------
# List *currency* stewardships of a *primid*:

def list_currency_stewardships(primid_id):
    primid_fph, primid_hrns, etypes, m = identify_entity(primid_id)
    if not primid_fph:
        return [], primid_id + " is not a registered identifier"
    if not ("primid" in etypes):
        return [], primid_hrns + " has no primid"
    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT cstewardships_fph_list FROM primids WHERE entity_fph = ?",
            (primid_fph,)
        )
        result = cursor.fetchone()
        if result is None:
            cstewardships_fph_list = []
        else:
            cstewardships_fph_list = list(set(pickle.loads(result[0])))
        # At the very least, the *primid* is a steward of the *currency* with
        # which it shares an identifier:
        if not (primid_fph in cstewardships_fph_list):
            cstewardships_fph_list.append(primid_fph)
        cstewardships_fph_blob = pickle.dumps(cstewardships_fph_list)
        cursor.execute(
            "UPDATE primids SET cstewardships_fph_list = ? " \
            + "WHERE entity_fph = ?",
            (cstewardships_fph_blob, primid_fph)
        )
        conn.commit()
        cursor.close()
    return cstewardships_fph_list, ""


#==============================================================================
#
# 2026-06-04:
#
# The steward and stewardship add/remove sections should be separated because
# the entities may be registered within different clades (and therefore in
# different SQLite files).


# A steward is added to or removed from the entity (*namespace* or *currency*):
#
def add_or_remove_steward(
        entity_id,          # HRNS or FPH identifier
        entity_type,        # namespace | currency
        operation,          # add | remove
        auth_steward_id,    # The steward authorizing the change
        other_steward_id    # The steward affected
    ):
    # Check that target entity identifier exists:
    entity_fph, entity_hrns, e_etypes, m = identify_entity(entity_id)
    if not entity_fph:
        return entity_id + " is not a registered identifier"
    # If so, does it identify an entity of the type specified above?
    if not (entity_type in e_etypes):
        return "Identifier " + entity_hrns + " has no " + entity_type

    # Check that the authorizing steward is a registered *primid*:
    auth_steward_fph, auth_steward_hrns, a_etypes, \
    m = identify_entity(auth_steward_id)
    if not auth_steward_fph:
        return auth_steward_id + " is not a registered identifier"
    if not ("primid" in a_etypes):
        return "Identifier " + auth_steward_id + " has no primid"

    # Check that the added/removed steward is a registered *primid*:
    other_steward_fph, other_steward_hrns, s_etypes, \
    m = identify_entity(other_steward_id)
    if not other_steward_fph:
        return other_steward_id + " is not a registered identifier"
    if not ("primid" in s_etypes):
        return "Identifier " + other_steward_id + " has no primid"

    # Check validity of entity type:
    if entity_type == "namespace":
        table = "namespaces"
    elif entity_type == "currency":
        table = "currencies"
    else:
        return "Type must be namespace or currency"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT stewards_fph_list FROM " + table + " WHERE entity_fph = ?",
            (entity_fph,)
        )
        result = cursor.fetchone()
        if result is None: # (Should never happen)
            # Self-repair should never be necessary, so this action is logged:
            stewards_fph_list = []
            stewards_fph_list.append(entity_fph)
            log_self_repair(entity_id, "Missing stewards list created")
        else:
            stewards_fph_list = pickle.loads(result[0])
            stewards_fph_list = list(set(stewards_fph_list))

        if (operation == "add"):
            if other_steward_fph in stewards_fph_list:
                cursor.close()
                return other_steward_fph + " already steward of " + entity_hrns
            else:
                stewards_fph_list.append(other_steward_fph)
        elif (operation == "remove") and (other_steward_fph != entity_fph):
            if not (other_steward_fph in stewards_fph_list):
                cursor.close()
                return other_steward_fph + " is not steward of " + entity_hrns
            else:
                stewards_fph_list.remove(other_steward_fph)
        else:
            cursor.close()
            return "(a) Invalid operation: " + operation

        # At the very least, the entity must have a steward *primid* with which
        # it shares an identifier:
        if not (entity_fph in stewards_fph_list):
            stewards_fph_list.append(entity_fph)

        # Control reaches this point if and only if a change has been made to
        # the the stewards list:
        if not (auth_steward_fph in stewards_fph_list):
            cursor.close()
            return auth_steward_hrns + " is not a steward of " + entity_hrns
        #
        if (auth_steward_fph in stewards_fph_list) \
        or (auth_steward_fph == entity_fph):
            cursor.execute(
                "UPDATE " + table + " SET stewards_fph_list = ? " \
                + "WHERE entity_fph = ?",
                (pickle.dumps(stewards_fph_list), entity_fph)
            )
            conn.commit()
            cursor.close()
    return "" # success

# An entity (*namespace* or *currency*) is added to or removed from a *primid*
# stewardships list:'
#
def add_or_remove_stewardship(
        entity_id,          # HRNS or FPH identifier
        entity_type,        # namespace | currency
        operation,          # add | remove
        auth_steward_id,    # The steward authorizing the change
        other_steward_id    # The steward affected
    ):
    # Check that the authorizing steward is a registered *primid*:
    auth_fph, auth_hrns, p_etypes, m = identify_entity(auth_steward_id)
    if not auth_fph:
        return auth_id + " is not a registered identifier"
    if not ("primid" in p_etypes):
        return "Identifier " + auth_hrns + " has no primid"

    # Check that the target entity identifer exists:
    entity_fph, entity_hrns, entity_etypes, m = identify_entity(entity_id)
    if not entity_fph:
        return entity_id + " is not a registered identifier"
    # If so, check that it identifies an entity of the specified type:
    if not (entity_type in entity_etypes):
        return "Identifier " + entity_hrns + " has no " + entity_type

    # Check validity of the specified entity type:
    if entity_type == "namespace":
        stewardships_col = "nstewardships_fph_list" # column label
        #
        active, open, sandbox, private, owner_fph, \
        parent_currency_fph, stewards_fph_list, \
        m = get_namespace_properties(entity_fph)
    elif entity_type == "currency":
        stewardships_col = "cstewardships_fph_list" # column label
        #
        currency_fph, currency_hrns, active, open, private, sandbox, \
        c_type, c_category, c_units, c_metrical_equivalence, c_dimensions, \
        prefix, suffix, default_account_name, \
        stewards_fph_list, m = get_currency_properties(entity_id)
    else:
        return "Invalid type specified: must be a namespace or currency"
    if not (auth_fph in stewards_fph_list):
        return "The primid " + auth_hrns \
               + " is not a steward of " + entity_type + " " + entity_hrns

    # Check that the added/removed steward is a registered *primid*:
    other_steward_fph, other_steward_hrns, p_etypes, \
    m = identify_entity(other_steward_id)
    if not other_steward_fph:
        return other_steward_id + " is not a registered identifier"
    if not ("primid" in p_etypes):
        return "Identifier " + other_steward_id + " has no primid"

    with sqlite3.connect(ENTITIES_DB) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT " + stewardships_col + " FROM primids " \
            + "WHERE entity_fph = ?",
            (other_steward_fph,)
        )
        result = cursor.fetchone()
        if result is None: # (should never happen)
            # Self-repair should never be necessary, so this action is logged:
            stewardships_fph_list = []
            log_self_repair(entity_id, "Missing stewardship list created")
        else:
            stewardships_fph_list = list(set(pickle.loads(result[0]))) # Note 2

        # At the very least, the steward *primid* must have stewardship of the
        # entities with which it shares an identifier:
        if not (entity_fph in stewardships_fph_list):
            stewardships_fph_list.append(entity_fph)
            cursor.execute(
                "UPDATE primids SET " + stewardships_col + " = ? " \
                + "WHERE entity_fph = ?",
                (pickle.dumps(stewardships_fph_list), entity_fph)
            )
            conn.commit()
            # Self-repair should never be necessary, so this action is logged:
            log_self_repair(entity_id, "Missing self-stewarded entity added")
        if operation == "add":
            stewardships_fph_list.append(entity_fph)
        elif operation == "remove":
            if entity_fph in stewardships_fph_list:
                stewardships_fph_list.remove(entity_fph)
        else:
            cursor.close()
            return "Invalid operation: " + operation
        stewardships_fph_blob = pickle.dumps(list(set(stewardships_fph_list)))
        cursor.execute(
            "UPDATE primids SET " + stewardships_col + " = ? " \
            + "WHERE entity_fph = ?",
            (stewardships_fph_blob, other_steward_fph)
        )
        conn.commit()
        cursor.close()
    return "" # success


def add_namespace_steward(entity_id, auth_steward_id, new_steward_id):
    print(
        "adding primid " + new_steward_id \
        + " as steward of namespace " + entity_id
    )
    m = add_or_remove_steward(
            entity_id, "namespace", "add", auth_steward_id, new_steward_id
        )
    print(
        "adding namespace " + entity_id \
        + " to stewardships of primid " + new_steward_id
    )
    n = add_or_remove_stewardship(
            entity_id, "namespace", "add", auth_steward_id, new_steward_id
        )
    return m + "\n" + n

def remove_namespace_steward(entity_id, auth_steward_id, other_steward_id):
    print(
        "removing primid " + other_steward_id \
        + " as steward of namespace " + entity_id
    )
    m = add_or_remove_steward(
            entity_id, "namespace", "remove", auth_steward_id, other_steward_id
        )
    print(
        "removing namespace " + entity_id \
        + " from stewardship of primid " + other_steward_id
    )
    n = add_or_remove_stewardship(
            entity_id, "namespace", "remove", auth_steward_id, other_steward_id
        )
    return m + "\n" + n

def add_currency_steward(entity_id, auth_steward_id, new_steward_id):
    print(
        "adding primid " + new_steward_id \
        + " as steward of currency " + entity_id
    )
    m = add_or_remove_steward(
            entity_id, "currency", "add", auth_steward_id, new_steward_id
        )
    print(
        "removing currency " + entity_id \
        + " from stewardship of primid " + new_steward_id
    )
    n = add_or_remove_stewardship(
            entity_id, "currency", "add", auth_steward_id, new_steward_id
        )
    return m + "\n" + n

def remove_currency_steward(entity_id, auth_steward_id, other_steward_id):
    print(
        "removing primid " + other_steward_id \
        + " as steward of currency " + entity_id
    )
    m = add_or_remove_steward(
            entity_id, "currency", "remove", auth_steward_id, other_steward_id
        )
    print(
        "removing currency " + entity_id \
        + " from stewardship of primid " + other_steward_id
    )
    n = add_or_remove_stewardship(
            entity_id, "currency", "remove", auth_steward_id, other_steward_id
        )
    return m + "\n" + n
