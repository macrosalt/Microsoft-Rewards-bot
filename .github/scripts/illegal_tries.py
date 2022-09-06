import json
import os

log_prefix = "log"

log_dir = os.path.abspath(os.path.join(os.path.abspath(__file__), "../../../logs"))
files= os.listdir(log_dir)
for file in files: 
    if os.path.isdir(file) or not file.startswith(log_prefix):
        continue
    with open(log_dir+"/"+file) as input:
        dict = json.load(input)
        for key, val in dict.items():
            check_situation = val["Last check"]
            if len(check_situation) != 10 or check_situation[0] != "2":
                print(f'account: {key} -> check:{check_situation} in {file}')