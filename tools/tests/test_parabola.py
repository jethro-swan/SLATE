#!/home/slate/SLATE/venv/bin/python3

from app.core.bpplot import account_balance_oscillation

#test_user = "bb.cc"

#test_account = "933fc872b76dc4904b4b7b69d4be5e92"
test_account = "7daf13381e185c407f102d8bf84f0446"

test_ahid = "ah050.bb.cc"
test_currency = "hrs.bb.cc"

b_imgpath, v_imgpath = account_balance_oscillation(test_ahid, test_currency)

#print(b_imgpath)
#print(v_imgpath)

#from matplotlib.pyplot import *
#from numpy import *
#x=linspace(-1,1,600)
#y=x**2
#plot(x,y)
##xlabel("x axis")
##ylabel("y axis")
##print(x)
#show()
