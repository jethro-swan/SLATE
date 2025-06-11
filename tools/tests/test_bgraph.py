#!/home/slate/SLATE/venv/bin/python3

from app.core.bgraph import currency_balance_graphs

test_currency = "hrs.bb.cc"

b_imgpath, v_imgpath = currency_balance_graphs(test_currency)

print(b_imgpath)
print(v_imgpath)
