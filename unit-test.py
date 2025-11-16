from collections import Counter
from handle_data import read_data

def count_values(data):
    counter = Counter()
    for item in data:
        for k, v in item.items():
            counter[k] += 1
    return counter

import json

in1 = read_data("data-Linh.csv")
in2 = read_data("data-QN.csv")

true_in1 = json.load(open("data-Linh.json", encoding="utf-8"))
true_in2 = json.load(open("data-QN.json", encoding="utf-8"))

if (count_values(in1) == count_values(true_in1)
    and count_values(in2) == count_values(true_in2)):
    print("All tests passed!")
else:
    print("Mismatch detected!")
    print("Linh diff:", count_values(in1) - count_values(true_in1))
    print("QN diff:", count_values(in2) - count_values(true_in2))