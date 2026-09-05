#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import new_namespace
from app.core.slate_core import get_namespace_properties

print()
namespace_hrns = "bb.cc"

for nsname in ["vv", "ww", "xx", "yy", "zz"]:
    namespace_fph, namespace_hrns, \
    m = new_namespace(
            nsname,
            namespace_hrns,
            "hrs.cc",
            "bb.cc",
            private=False
        )
    if m:
        print("!!!! " + m)
    print(namespace_fph + " = " + namespace_hrns)

    active, open, sandbox, private, owner_fph, currency_fph, stewards_list, \
    m = get_namespace_properties(namespace_hrns)
    if m:
        print("!!!!!!!! " + m)
    print(namespace_hrns)
    print("stewards_list: ", end="")
    print(stewards_list)
    print()
