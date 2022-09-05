import sys, json

dict = json.load(sys.stdin)
for key, val in dict.items():
    check_situation = val["Last check"]
    if len(check_situation) != 10 or check_situation[0] != "2":
        print(f'account: {key} -> check:{check_situation}')