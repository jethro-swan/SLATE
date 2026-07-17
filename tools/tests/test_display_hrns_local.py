#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import display_hrns_local

hrns = [
    "bb.cc",
    "ah1.bb.cc",
    "uu.vv.ww.xx.yy.zz.bb.cc",
    "ah1.cthulhu.cc",
    "r04.sand.box.cc"
]

for i in range(len(hrns)):
    print("entity HRNS = " + hrns[i])
    truncated_hrns, clade_hrns, m = display_hrns_local(hrns[i])
    print("truncated HRNS = " + truncated_hrns)
    print("clade HRNS = " + clade_hrns)
    print()
