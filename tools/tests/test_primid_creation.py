#!/home/slate/SLATE/venv/bin/python3

from app.core.fph_hrns_maps import hrns_to_fph
from app.core.fph_hrns_maps import record_private_namespace_root
from app.core.slate_core import new_primid
from app.core.slate_core import get_hub_mode
from app.core.slate_core import new_pairing

p_fph, m = hrns_to_fph("cc")

hub_mode = get_hub_mode()

currencies = ["cc", "hrs.cc", "kwh.cc"] # the seed *currencies*

print("="*160)
pn = ["uu", "vv", "ww", "xx", "yy", "zz"]
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

    #print("-"*160)

#    for currency_hrns in currencies:
#        print("pairing " + currency_hrns + " & " + primid_hrns)
#        a_fph = new_pairing(primid_fph, primid_hrns, currency_hrns)##

        #print("-"*160)

    #print("="*160)
    print("-"*160)
