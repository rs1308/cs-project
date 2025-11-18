import pickle

with open("orders.dat", "rb") as f:
    data = pickle.load(f)

for order in data:
    print(order)
    print("------------------------------")

