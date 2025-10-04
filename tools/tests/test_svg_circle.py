#!/home/slate/SLATE/venv/bin/python3

from app.core.ahid_circle import accounts_circle
#from app.core.ahid_circle import plot_accounts_circle

currency_hrns = "kwh.cc"

accounts_d, m = accounts_circle(currency_hrns)

print(accounts_d)

#plot_accounts_circle(currency_hrns)
