#!/home/slate/SLATE/venv/bin/python3


from app.core.bgraph2 import create_balvol_plot
from app.core.bgraph import currency_balance_graphs

test_currency = "hrs.cc"
test_ahid = "bb.cc"


plot_filename = create_balvol_plot(currency_id, ahid_id, False)





#b_imgpath, v_imgpath = currency_balance_graphs(test_currency)
#print(b_imgpath)
#print(v_imgpath)
