#!/home/slate/SLATE/venv/bin/python3

from app.core.fph_hrns_maps import hrns_to_fph
from app.core.slate_core import record_private_namespace_root
from app.core.slate_core import new_primid
from app.core.slate_core import get_hub_mode
from app.core.slate_core import new_pairing
from app.core.slate_core import get_primid_properties
from app.core.slate_core import get_namespace_properties

p_fph, m = hrns_to_fph("cc")

hub_mode = get_hub_mode()

currencies = ["cc", "hrs.cc", "kwh.cc"] # the seed *currencies*

print("="*120)
#pn = ["uu", "vv", "ww", "xx", "yy", "zz"]
pn = ["a1", "a2", "a3", "a4", "a5"]
for p in pn:

    primid_fph, primid_hrns, access_token, \
    m = new_primid(
            p, p_fph,
            p.upper(), "john@lrc.org.uk", "", "zxcvbnm", "123456",
            "kwh.cc"
        )
    record_private_namespace_root(primid_fph, primid_fph)
    if m:
        print(m)

    print(primid_fph + " = " + primid_hrns)
    active, administrator, \
    ahids_fph_list, accounts_fph_list, pmap, \
    nstewardships_fph_list, cstewardships_fph_list, \
    m = get_primid_properties(primid_hrns)
    print("active = " + str(active))
    print("administrator = " + str(administrator))
    print("ahids_fph_list", end="")
    print(ahids_fph_list)
    print("accounts_fph_list", end="")
    print(accounts_fph_list)
    print("pmap", end="")
    print(pmap)
    print("nstewardships_fph_list", end="")
    print(nstewardships_fph_list)
    print("cstewardships_fph_list", end="")
    print(cstewardships_fph_list)
    print("\n\nnamespace:")
    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(primid_hrns)
    if m:
        print("!!!!!!!! " + m)
    print("active = " + str(active))
    print("open = " + str(open))
    print("sandbox = " + str(sandbox))
    print("private = " + str(private))
    print("owner_fph = " + owner_fph)
    print("currency_fph = " + currency_fph)
    print("stewards_list", end="")
    print(stewards_list)
    print("stewards_list: ", end="")
    print()
    print("-"*120)
