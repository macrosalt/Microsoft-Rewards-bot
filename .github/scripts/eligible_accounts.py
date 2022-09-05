import sys, json

point_bar = 9100
dict = json.load(sys.stdin)
for key, val in dict.items():
    if val["Points"] > point_bar:
        print(f'account: {key} -> points:{val["Points"]}')