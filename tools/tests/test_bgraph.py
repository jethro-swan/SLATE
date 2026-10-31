#!/home/slate/SLATE/venv/bin/python3

from app.core.constants import GRAPHS
from app.core.bgraph2 import create_balvol_plot
from app.core.bgraph import currency_balance_graphs

test_currency = "hrs.cc"
test_ahid = "ah1.bb.cc"


plot_filepath, graph_path = create_balvol_plot(test_currency, test_ahid, True)

print(plot_filepath)
print(graph_path)



#b_imgpath, v_imgpath = currency_balance_graphs(test_currency)
#print(b_imgpath)
#print(v_imgpath)
