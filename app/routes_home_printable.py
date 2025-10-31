# login landing page ----------------------------------------------------------
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    page = "home"
    group = "home"

    namespace_steward = False
    currency_steward = False
    paying = False
    logged_in = current_user.is_authenticated

    identity_fph = current_user.get_id() # *primid* as which logged in
    identity_hrns = fph_to_hrns(identity_fph)
    identity_type = fph_to_display_type(identity_fph)

    # The user logs in as the *primid*, even if indirectly as one of its
    # *secid*s, but once logged in will see all of its *identities* along with
    # a list of *accounts* belonging to each. The user will also see a list of
    # entities over which it holds/shares stewardship.

    stewardships_list, m = list_stewardships(identity_fph)

    print("Currently in the /home endpoint")
    print("identity_fph = " + identity_fph)
    print("identity_hrns = " + identity_hrns)
    print("identity_type = " + identity_type)

    # Since a user may have *accounts* scattered across an arbitrary number of
    # *namespaces*, it is necessary to maintain a list of these:

    # A full list of *identities* is compiled, with the *primid* first:
    identities_list = list_secids(identity_fph)
    identities_list.insert(0, identity_fph)

    identities = [] # list of *identities* to pass to "home.html" template as
                    # dictionaries.

    for id_fph in identities_list:

        id = {} # the outer dictionary for this *identity*

        id_fph, \
        id_hrns, \
        etype, \
        m = identify_entity(id_fph)
        if m:
            flash(m)

        id["fph"] = id_fph
        id["hrns"] = fph_to_hrns(id_fph)
        id["type"] = etype

        accounts_list, m = list_agent_accounts(id_fph)
        if m:
            flash(m)

        # List the *accounts* belonging to this *identity*:
        accounts = {} # (second-level dictionary for iteration in template)
        for account_fph in accounts_list:
            # Fetch account details:
            account_currency_fph, \
            account_owner_fph, \
            account_balance, \
            m = get_account_specific_properties(account_fph)
            # Fetch currency details:
            currency_fph, \
            currency_hrns, \
            prefix, \
            suffix, \
            stewards_list, \
            m = get_currency_specific_properties(account_currency_fph)
            # Assemble a dictonary of *account* properties:
            a = {}
            a["fph"] = account_fph
            a["hrns"] = fph_to_hrns(account_fph)
            a["owner_fph"] = account_owner_fph
            a["owner_hrns"] = fph_to_hrns(account_owner_fph)
            a["balance"] = integer_to_money_format(account_balance)
            a["isneg"] = (account_balance < 0)
            a["prefix"] = prefix
            a["suffix"] = suffix
            primid_currency_steward = currency_fph in stewardships_list
            a["primid_is_currency_steward"] = primid_currency_steward
            #if currency_fph in stewardships_list:
            #    a["primid_is_currency_steward"] = True
            #else:
            #    a["primid_is_currency_steward"] = False
            a["currency_fph"] = currency_fph
            a["currency_hrns"] = currency_hrns
            accounts[id_fph] = accounts
        id["accounts"] = accounts
        identities.append(id)


    # If this is a *primid*, fetch a list of its *secid*s and stewardships:
    secid_list = list_secids(identity_fph)
    secids = []
    print("secids for " + fph_to_hrns(identity_fph))
    for secid_fph in secid_list:
        if secid_fph != "":
            print(identity_fph + " :: " + fph_to_hrns(secid_fph))
            secid = {}
            secid["fph"] = secid_fph
            secid["hrns"] = fph_to_hrns(secid_fph)
            secids.append(secid)

    #stewardships_list, m = list_stewardships(identity_fph)
    stewardships = []
    print("stewardships for " + fph_to_hrns(identity_fph))
    for stewardship_fph in stewardships_list:
        if stewardship_fph != "":
            print(identity_fph + " :: " + fph_to_hrns(stewardship_fph))
            stewardship = {}
            entity_fph, \
            entity_hrns, \
            etype, \
            m = identify_entity(stewardship_fph)
            stewardship["fph"] = stewardship_fph
            stewardship["hrns"] = entity_hrns
            stewardship["etype"] = etype
            stewardships.append(stewardship)

    return render_template(
                "home.html",
                title="Home",
                page=page,
                group=group,
                development_mode=development_mode,
                logged_in=logged_in,
                #namespace_steward=namespace_steward,
                #currency_steward=currency_steward,

                # Variables passed for display in "base.html":
                identity_type=identity_type,
                identity_fph=identity_fph,
                identity_hrns=identity_hrns,

                # List of (nested) dictionaries for display in "home.html":
                identities=identities,
                #accounts=accounts,
                secids=secids,
                stewardships=stewardships
            )
