#!/home/slate/SLATE/venv/bin/python3

from app.core.slate_core import list_currency_accounts
from app.core.slate_core import get_account_currency
from app.core.slate_core import get_account_specific_properties
from app.core.slate_core import identify_entity
from app.core.constants import GRAPHS


test_currency = "cc"

account_fph_list = list_currency_accounts(test_currency)

#account = {}
#accounts = []
balances = []
sum = 0
a = []
x_ = 1
b_max = b_min = 0
for account_fph in account_fph_list:
    currency_fph, \
    owner_fph, \
    ahid_fph, \
    balance, \
    volume, \
    m = get_account_specific_properties(account_fph)
    balances.append(balance)
    if balance < b_min:
        b_min = balance
    if balance > b_max:
        b_max = balance
    a.append(str(x_))
    x_ += 1
balances.sort()

for balance in balances:
    print(balance)

print(a)

# importing the modules
from bokeh.models import ColumnDataSource
from bokeh.palettes import Bright6
from bokeh.plotting import figure, show

source = ColumnDataSource(
            data = dict(
                       a = a,
                       balance = balances,
                       color = Bright6
                   )
         )

p = figure(
        x_range = a,
        height = 600,
        toolbar_location = None,
        tools = ""
    )

p.vbar(
    x = a,
    top = balances,
    line_color = "#ffffff",
    width = 0.9
)

#p.y_range.start = b_min
#p.y_range.end = b_max
p.x_range.range_padding = 0.0
#p.xgrid.grid_line_color = None
#p.legend.location = "top_center"
#p.legend.orientation = "horizontal"

show(p)
