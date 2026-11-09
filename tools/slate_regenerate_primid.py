#!/home/slate/SLATE/venv/bin/python3




from app.core.fph_hrns_maps import hrns_to_fph
#from app.core.fph_hrns_maps import record_private_namespace_root
from app.core.slate_core import record_private_namespace_root
from app.core.slate_core import new_primid
from app.core.slate_core import get_hub_mode
from app.core.slate_core import new_pairing
from app.core.slate_core import split_hrns

import argparse


ap = argparse.ArgumentParser(description = "Lazy creation of login identity")
# The whole *primid* HRNS is used.
ap.add_argument(
    "-p", "--primid-hrns", dest = "primid_hrns", action = "store",
    help = "Login identity of user"
)
ap.add_argument(
    "-w", "--password", dest = "password", action = "store",
    help = "Login password"
)
ap.add_argument(
    "-P", "--pin", dest = "pin", action = "store",
    help = "Login PIN"
)
args = ap.parse_args()

if args.primid_hrns is None:
    ap.print_help()
    sys.exit(1)
else:
    primid_hrns = args.primid_hrns
    name, parent_hrns = split_hrns(primid_hrns)

if args.password is None:
    ap.print_help()
    sys.exit(1)
else:
    password = args.password

if args.pin is None:
    ap.print_help()
    sys.exit(1)
else:
    pin = args.pin




p_fph, m = hrns_to_fph("cc") # parent of new *primid*

hub_mode = get_hub_mode()

#currencies = ["cc", "hrs.cc", "kwh.cc"] # the seed *currencies*
currencies = [
    "cc.cc",
    "hrs.cc",
    "kwh.cc",
    "h.hrs.cc",
    "m.hrs.cc",
    "ta.cc"
] # seed *currencies*

print("="*80)
pn = ["bb", "dd", "ee", "jw"]
for p in pn:
    primid_fph, primid_hrns, access_token, \
    m = new_primid(
            p, p_fph,
            "JW", "john@lrc.org.uk", "", "zxcvbnm", "123456",
            "hrs.cc"
        )
    record_private_namespace_root(primid_fph, primid_fph)
    if m:
        print(m)
    for currency_hrns in currencies:
        print("pairing " + currency_hrns + " & " + primid_hrns)
        a_fph = new_pairing(primid_fph, primid_hrns, currency_hrns)
    print("-"*80)
