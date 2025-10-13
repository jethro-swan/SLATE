#!/home/slate/SLATE/venv/bin/python3

from app.core.ahid_circle import accounts_circle
#from app.core.ahid_circle import plot_accounts_circle

#currency_hrns = "cc"
#currency_hrns = "bits.bb.cc"
currency_hrns = "kwh.cc"
currency_hrns = "hrs.cc"
#currency_hrns = "zz.bb.cc"

accounts_d, m = accounts_circle(currency_hrns, "bb.cc")

#print(accounts_d)

#plot_accounts_circle(currency_hrns)
