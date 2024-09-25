
# Account balances are stored as integers, assuming cents (euros or dollars) or
# pence (sterling) to be the smallest value.
def integer_to_money_format(amount):
    return "{:10.2f}".format(amount/100)
