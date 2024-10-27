grep 'create_entities_db()' app/core/*.py
grep 'add_entity_common_properties' app/core/*.py
grep 'get_entity_common_properties(entity_id)' app/core/*.py
grep 'entity_is_active(entity_id)' app/core/*.py
grep 'get_entity_type(entity_fph)' app/core/*.py
grep 'add_account_to_currency' app/core/*.py
grep 'add_primid_specific_properties' app/core/*.py
grep 'update_primid_contact_details' app/core/*.py
grep 'update_primid_access_details' app/core/*.py
grep 'add_primid_stewardships' app/core/*.py
grep 'add_currency_specific_properties' app/core/*.py
grep 'add_namespace_specific_properties' app/core/*.py
grep 'add_account_specific_properties' app/core/*.py
grep 'get_account_specific_properties(account_fph)' app/core/*.py
grep 'account_status(account_fph)' app/core/*.py
grep 'namespace_status(namespace_fph)' app/core/*.py
grep 'new_primid' app/core/*.py
grep 'new_secid' app/core/*.py
grep 'new_namespace' app/core/*.py
grep 'new_currency' app/core/*.py
grep 'new_account' app/core/*.py
grep 'get_currency_name(currency_fph)' app/core/*.py
grep 'set_web_password_hash(primid_fph, password)' app/core/*.py
grep 'primid_update_realname(primid_fph, new_name)' app/core/*.py
grep 'primid_update_email(primid_fph, new_email)' app/core/*.py
grep 'primid_update_login(primid_fph, new_password, new_pin)' app/core/*.py
grep 'list_primid_accounts(primid_fph)' app/core/*.py
grep 'get_account_currency(account_fph)' app/core/*.py
grep 'list_currency_accounts(currency_identifier)' app/core/*.py
grep 'list_primid_currency_accounts(primid_fph, currency_fph)' app/core/*.py
grep 'list_primid_currencies(primid_fph)' app/core/*.py
grep 'get_parent_namespace(entity_fph)' app/core/*.py
grep 'list_child_namespaces(namespace_fph)' app/core/*.py
grep 'list_all_namespaces(root_namespace_fph)' app/core/*.py
grep 'list_currencies_in_namespace(namespace_fph = "")' app/core/*.py
grep 'list_primids_in_namespace(namespace_fph = "")' app/core/*.py
grep 'list_accounts_in_namespace(namespace_fph = "")' app/core/*.py
grep 'list_namespaces_in_namespace(namespace_fph = "")' app/core/*.py
grep 'list_namespaces_below_namespace(namespace_fph = "")' app/core/*.py
grep 'move_entity(entity_fph, destination_namespace_fph)' app/core/*.py
grep 'list_currencies_in_common_by_fph(a1_fph, a2_fph)' app/core/*.py
grep 'list_currencies_in_common_by_hrns(a1_fph, a2_fph)' app/core/*.py
grep 'identify_entity(entity_identifier)' app/core/*.py
grep 'add_stewards(entity_fph, *primids_fph)' app/core/*.py
grep 'add_stewardship(primid_fph, entity_fph)' app/core/*.py
grep 'remove_stewards(entity_fph, *primids_fph)' app/core/*.py
grep 'remove_stewardship(primid_fph, entity_fph)' app/core/*.py
grep 'list_stewards(entity_fph)' app/core/*.py
grep 'list_stewardships(primid_fph)' app/core/*.py
grep 'list_active_namespaces(ancestor_namespace_identifier = "")' app/core/*.py
grep 'get_primid(secid_id)' app/core/*.py
grep 'list_primids(status)' app/core/*.py
