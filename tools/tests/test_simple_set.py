#!/home/slate/SLATE/venv/bin/python3

from app.core.small_set import *

n_iterations = 100

bal_worst, \
bal_lt, \
bal, \
journal = create_simple_set()

print("\nbal_worst")
for w in range(len(bal_worst)):
    print(str(bal_worst[w]) + " ", end="")
print("\n\nbal_lt")
for l in range(len(bal_lt)):
    print(str(bal_lt[l]) + " ", end="")
print("\n\nbal")
for a in range(n_agents):
    for c in range(n_currencies):
        


#for c in range(len(bal)):
#    for a in range(len(bal[c])):
        print(str(bal[c][a]) + " ", end="")
    print()
print("\n\njournal")
for b in range(len(journal)):
    print(journal[b])
print()




bal_worst, \
bal_lt, \
bal, \
journal = all_iterations(n_iterations, bal_worst, bal_lt, bal, journal)

print("n_currencies = " + str(n_currencies))
print("n_agents = " + str(n_agents))

for c in range(n_currencies):
    for a in range(n_agents):
        print(str(c) + " : " + str(a))
