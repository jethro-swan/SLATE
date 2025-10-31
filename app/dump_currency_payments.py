#!/usr/bin/env python3

from core.payments import dump_currency_payments_csv
from core.payments import dump_account_payments_csv


cpath, m = dump_currency_payments_csv("vvv.sog.fjq.de")
print(cpath)
print(m)
print()
print("vvv.sog.fjq.de ::")
print()

apath, m = dump_account_payments_csv("iop.nr.gar.cc")
print(apath)
print(m)
print()
print("qqq.nr.gar.cc ::")
print()
apath, m = dump_account_payments_csv("qqq.nr.gar.cc")
print(apath)
print(m)
print()
