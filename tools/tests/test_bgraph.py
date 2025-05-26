#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import list_currency_accounts
from app.core.slate_core import get_account_currency
from app.core.slate_core import get_account_specific_properties
from app.core.slate_core import identify_entity


test_currency = "hrs.cc.bb.cc"

account_fph_list = list_currency_accounts(test_currency)

#account = {}
#accounts = []
balances = []
sum = 0

for account_fph in account_fph_list:

    currency_fph, \
    owner_fph, \
    ahid_fph, \
    balance, \
    volume, \
    m = get_account_specific_properties(account_fph)

    balances.append(balance)

    #print(balance)

balances.sort()

for balance in balances:
    print(balance)

# importing the modules
from bokeh.plotting import figure, output_file, show

# file to save the model
output_file("/var/www/gfg.html")

# instantiating the figure object
graph = figure(title = "Bokeh Vertical Bar Graph")

# x-coordinates to be plotted
x = [1, 2, 3, 4, 5]

# x-coordinates of the top edges
top = [1, 2, 3, 4, 5]

# width / thickness of the bars
width = 0.5

# plotting the graph
graph.vbar(x,
           top = top,
           width = width)

# displaying the model
show(graph)
